from get_game_board import get_game_board
from identify_game_version import identify_game_version
from word_finder import find_words, find_anagrams, print_found_words, print_anagram_words, find_word_bites_words, print_word_bites_moves, WordBitesMove, are_words_related
from word_drawer import draw_word, click_anagram_word, execute_word_bites_move
from press_start_button import focus_and_click_start
import time
import signal
from concurrent.futures import ThreadPoolExecutor
import heapq
from dataclasses import dataclass, field
from typing import Tuple, List
import os
from threading import Lock
from config import GAME_DURATION
import traceback

WORDS_FOUND = 0
GAME_VERSION = "unknown"
TIME_REMAINING = 90  # Track time remaining
START_TIME = 0  # Track start time globally

@dataclass(order=True)
class PrioritizedWord:
    priority: int
    word: str = None
    path: List[Tuple[int, int]] = None
    
    def __init__(self, word: str, path: List[Tuple[int, int]]):
        self.priority = -len(word)  # Negative length for max-heap behavior
        self.word = word
        self.path = path

@dataclass(order=True)
class PrioritizedWordBitesMove:
    priority: int
    move: WordBitesMove = field(compare=False)
    
    def __init__(self, move: WordBitesMove):
        self.priority = -move.score  # Negative score for max-heap behavior (highest score first)
        self.move = move

def timeout_handler(signum, frame):
    print("\nTime's up! Game summary:")
    print("------------------------")
    print(f"Game version: {GAME_VERSION}")
    print(f"Words found: {WORDS_FOUND}")
    print(f"Time played: {GAME_DURATION} seconds")
    print("Program terminated.")
    os._exit(0)

def update_time_remaining():
    global TIME_REMAINING
    TIME_REMAINING = max(0, GAME_DURATION - (time.time() - START_TIME))

def main():
    try:
        global START_TIME
        START_TIME = time.time()
        words_found = 0
        
        if not focus_and_click_start():
            print("Failed to start game")
            return
            
        time.sleep(1)
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(GAME_DURATION)
        
        # First identify the game version
        try:
            game_version = identify_game_version()
            print(f"Detected game version: {game_version}")
            if game_version.startswith('unknown'):
                print("Failed to identify game version")
                return
        except Exception as e:
            print(f"Failed to identify game version: {str(e)}")
            return
        
        # Get the actual game board from screenshot
        try:
            board = get_game_board(game_version)
        except Exception as e:
            print(f"Failed to capture game board: {str(e)}")
            return

        if board:
            print("Game Board:")
            if game_version == "WORD_BITES":
                print(board)  # Use the board's string representation
                # Find all possible words and their moves
                moves = find_word_bites_words(board)
                words_found = len(moves)
                
                # Print all found words and their required moves
                print_word_bites_moves(moves)
                
                # Use a priority queue and ThreadPoolExecutor for Word Bites
                move_queue = []
                heap_lock = Lock()
                
                with ThreadPoolExecutor(max_workers=1) as executor:
                    # Start the executor to process moves from the heap
                    draw_future = executor.submit(execute_word_bites_moves_from_heap, move_queue, heap_lock, board)
                    
                    # Add all moves to the priority queue
                    for move in moves:
                        with heap_lock:
                            heapq.heappush(move_queue, PrioritizedWordBitesMove(move))
                    
                    # Add sentinel value to signal completion
                    with heap_lock:
                        heapq.heappush(move_queue, PrioritizedWordBitesMove(WordBitesMove("", [], 0)))
                    
                    # Wait for all moves to be processed
                    draw_future.result()
                
            elif game_version.startswith('ANAGRAM'):
                # Print the anagram board
                print(' '.join(board[0]))  # Anagram board is a single row
                found_words = find_anagrams(board, min_length=3)
                words_found = len(found_words)
                
                sorted_words = sorted(found_words.keys(), key=lambda x: (-len(x), x))
                
                for word in sorted_words:
                    click_anagram_word(word, board, game_version)
                    time.sleep(0.005)  # Further reduced delay between words
                
                print_anagram_words(found_words)
            else:
                # Print the word hunt board
                for row in board:
                    print(' '.join(row))
                # For word hunt games, use existing drawing logic
                word_queue = []
                word_paths = {}
                heap_lock = Lock()
                
                with ThreadPoolExecutor(max_workers=1) as executor:
                    draw_future = executor.submit(draw_words_from_heap, word_queue, heap_lock, game_version)
                    
                    for word, path in find_words(board, game_version):
                        if word not in word_paths:
                            word_paths[word] = path
                            words_found += 1
                            with heap_lock:
                                heapq.heappush(word_queue, PrioritizedWord(word, path))
                    
                    with heap_lock:
                        heapq.heappush(word_queue, PrioritizedWord("", []))  # Sentinel value
                    
                    draw_future.result()
                
                print_found_words(word_paths)
            
            # Update global variables for timeout handler
            global WORDS_FOUND, GAME_VERSION
            WORDS_FOUND = words_found
            GAME_VERSION = game_version
            
        else:
            print("Failed to get game board")
            
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
        os._exit(0)
    finally:
        signal.alarm(0)

def draw_words_from_heap(word_heap: List[PrioritizedWord], heap_lock: Lock, game_version: str) -> None:
    """Draw words as they become available in the heap, longest first"""
    while True:
        with heap_lock:
            if not word_heap:
                time.sleep(0.1)
                continue
            
            prioritized_word = heapq.heappop(word_heap)
        
        # Check for sentinel value
        if not prioritized_word.path:
            break
            
        # Draw the word directly
        draw_word(prioritized_word.path, game_version)

def execute_word_bites_moves_from_heap(move_heap: List[PrioritizedWordBitesMove], heap_lock: Lock, board) -> None:
    """Execute Word Bites moves as they become available in the heap, highest score first"""
    # Keep track of the last successfully formed word and its block positions
    last_word = None
    last_word_blocks = {}  # Maps position -> block
    
    while True:
        with heap_lock:
            if not move_heap:
                time.sleep(0.1)
                continue
            
            prioritized_move = heapq.heappop(move_heap)
        
        # Check for sentinel value
        if not prioritized_move.move.word:
            break
        
        move = prioritized_move.move
        
        # Check if we can build upon the previous word
        if last_word and are_words_related(last_word, move.word):
            # Try to identify which blocks need to be added to form the new word
            if move.word.startswith(last_word):
                # The new word is an extension of the last word (e.g., "PLAY" -> "PLAYER")
                suffix = move.word[len(last_word):]
                
                # Create a modified move that only includes the new blocks needed
                modified_block_moves = []
                for block, target_pos in move.block_moves:
                    # Skip blocks that are already in position from the previous word
                    if target_pos not in last_word_blocks:
                        modified_block_moves.append((block, target_pos))
                
                if modified_block_moves:
                    # Create a new move with just the blocks we need to add
                    from word_finder import WordBitesMove
                    modified_move = WordBitesMove(move.word, modified_block_moves, move.score)
                    success = execute_word_bites_move(modified_move, board, True)
                else:
                    # If no new blocks needed (shouldn't happen), use the original move
                    success = execute_word_bites_move(move, board, True)
            
            elif last_word.startswith(move.word):
                # The new word is a prefix of the last word (e.g., "PLAYER" -> "PLAY")
                # This is less common but possible
                success = True  # No need to do anything, the word is already formed
            
            else:
                # The words are related but one is not a prefix of the other
                # (e.g., "PLAY" -> "PLAYING" where we need to remove 'Y' and add 'YING')
                success = execute_word_bites_move(move, board, True)
        else:
            # No previous word or words are not related, execute normally
            success = execute_word_bites_move(move, board, True)
        
        if success:
            # Update the last word and its block positions
            last_word = move.word
            last_word_blocks = {}
            for block, pos in move.block_moves:
                # Find the actual block at this position
                actual_block = board.get_block_at(pos[0], pos[1])
                if actual_block:
                    last_word_blocks[pos] = actual_block
            
            # Use a shorter delay between words
            time.sleep(0.03)  # Reduced delay between words
        else:
            # If we fail to form a word, wait a bit before trying the next one
            time.sleep(0.03)  # Reduced delay after failure
            # Reset last word tracking since we failed
            last_word = None
            last_word_blocks = {}

if __name__ == "__main__":
    main() 