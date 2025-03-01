from get_game_board import get_game_board
from identify_game_version import identify_game_version
from word_finder import find_words, find_anagrams, print_found_words, print_anagram_words, find_word_bites_words, print_word_bites_moves, WordBitesMove, are_words_related, optimize_word_order
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
        # Negative score for max-heap behavior (highest score first)
        self.priority = -move.score
        
        # Prioritize vertical words of the same length/score
        # This ensures vertical words with the same score as horizontal words
        # will be processed first, without changing their actual score
        if move.is_vertical:
            # Use a small priority boost that doesn't affect the actual score
            self.priority -= 0.1  # Subtract a small value to increase precedence
            
        self.move = move

def timeout_handler(signum, frame):
    # Calculate time elapsed
    time_elapsed = time.time() - START_TIME
    
    print("\nTime's up! Game summary:")
    print("------------------------")
    if GAME_VERSION == "unknown":
        print("Game version: Unknown - Game identification failed or timed out")
    else:
        print(f"Game version: {GAME_VERSION}")
    print(f"Words found: {WORDS_FOUND}")
    print(f"Time played: {time_elapsed:.1f} seconds (of {GAME_DURATION} seconds)")
    print("Program terminated.")
    os._exit(0)

def update_time_remaining():
    global TIME_REMAINING
    TIME_REMAINING = max(0, GAME_DURATION - (time.time() - START_TIME))

def main():
    try:
        global START_TIME, WORDS_FOUND, GAME_VERSION
        words_found = 0
        
        print("Starting game...")
        if not focus_and_click_start():
            print("Failed to start game - Could not find or click the start button")
            return
            
        print("Waiting for game to load...")
        time.sleep(2)  # Increased delay to ensure game is fully loaded
        
        signal.signal(signal.SIGALRM, timeout_handler)
        
        # First identify the game version
        try:
            print("Identifying game version...")
            game_version = identify_game_version()
            
            # Handle the case where identify_game_version returns None
            if game_version is None:
                print("Failed to identify game version - No iPhone window found")
                GAME_VERSION = "unknown - No iPhone window"
                return
            
            GAME_VERSION = game_version
            
            print(f"Detected game version: {game_version}")
            if game_version.startswith('unknown'):
                print("Failed to identify game version - Unknown game type")
                return
        except Exception as e:
            print(f"Failed to identify game version: {str(e)}")
            print(f"Error details: {traceback.format_exc()}")
            GAME_VERSION = f"unknown - Error: {str(e)}"
            return
        
        # Get the actual game board from screenshot
        try:
            print(f"Capturing game board for {game_version}...")
            board = get_game_board(game_version)
        except Exception as e:
            print(f"Failed to capture game board: {str(e)}")
            print(f"Error details: {traceback.format_exc()}")
            return

        if board:
            print("Game Board captured successfully!")
            
            # Start the timer now that all setup is complete and gameplay is about to begin
            START_TIME = time.time()
            signal.alarm(GAME_DURATION)
            print(f"Starting gameplay timer ({GAME_DURATION} seconds)...")
            
            if game_version == "WORD_BITES":
                print(board)  # Use the board's string representation
                
                # First, find all possible words before starting to move any letters
                print("Finding all Word Bites words first...")
                all_moves = list(find_word_bites_words(board))
                words_found = len(all_moves)
                WORDS_FOUND = words_found
                print(f"Found a total of {words_found} possible Word Bites words")
                
                # Optimize the word order for maximum efficiency
                print("Optimizing word order...")
                optimized_moves = optimize_word_order(all_moves)
                
                # Now set up the queue and start executing moves
                move_queue = []
                heap_lock = Lock()
                
                # Add all moves to the queue at once
                for move in optimized_moves:
                    with heap_lock:
                        heapq.heappush(move_queue, PrioritizedWordBitesMove(move))
                
                print("Starting to form words...")
                # Add sentinel value to signal completion
                with heap_lock:
                    heapq.heappush(move_queue, PrioritizedWordBitesMove(WordBitesMove("", [], 0)))
                
                # Now execute all the moves without any other processing happening
                print("Executing all moves...")
                execute_word_bites_moves_from_heap(move_queue, heap_lock, board)
                
            elif game_version.startswith('ANAGRAM'):
                # Print the anagram board
                print(' '.join(board[0]))  # Anagram board is a single row
                print("Finding anagrams...")
                found_words = find_anagrams(board, min_length=3)
                words_found = len(found_words)
                # Update global WORDS_FOUND for anagrams
                WORDS_FOUND = words_found
                
                print(f"Found {words_found} anagrams. Starting to click words...")
                sorted_words = sorted(found_words.keys(), key=lambda x: (-len(x), x))
                
                for i, word in enumerate(sorted_words):
                    if i % 10 == 0:  # Print progress every 10 words
                        print(f"Processed {i}/{len(sorted_words)} words...")
                    click_anagram_word(word, board, game_version)
                    time.sleep(0.01)  # Slightly increased delay between words
                
                print_anagram_words(found_words)
            else:
                # Print the word hunt board
                for row in board:
                    print(' '.join(row))
                # For word hunt games, use existing drawing logic
                word_queue = []
                word_paths = {}
                heap_lock = Lock()
                
                print(f"Starting word hunt for {game_version}...")
                with ThreadPoolExecutor(max_workers=1) as executor:
                    draw_future = executor.submit(draw_words_from_heap, word_queue, heap_lock, game_version)
                    
                    for word, path in find_words(board, game_version):
                        if word not in word_paths:
                            word_paths[word] = path
                            words_found += 1
                            # Update global WORDS_FOUND as we find words
                            WORDS_FOUND = words_found
                            with heap_lock:
                                heapq.heappush(word_queue, PrioritizedWord(word, path))
                            
                            if words_found % 20 == 0:  # Print progress every 20 words
                                print(f"Found {words_found} words so far...")
                    
                    print(f"Found a total of {words_found} words. Starting to draw words...")
                    with heap_lock:
                        heapq.heappush(word_queue, PrioritizedWord("", []))  # Sentinel value
                    
                    draw_future.result()
                
                print_found_words(word_paths)
            
        else:
            print("Failed to get game board - Board detection returned None")
            
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
        os._exit(0)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        print(f"Error details: {traceback.format_exc()}")
        os._exit(1)
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
    
    # Stats tracking
    vertical_words_count = 0
    horizontal_words_count = 0
    total_score = 0
    
    # Process counter for progress reporting
    processed_count = 0
    total_moves = len(move_heap) - 1  # Subtract 1 for sentinel
    
    while True:
        with heap_lock:
            if not move_heap:
                time.sleep(0.05)  # Reduced sleep time
                continue
            
            prioritized_move = heapq.heappop(move_heap)
        
        # Check for sentinel value
        if not prioritized_move.move.word:
            # Print final stats before exiting
            print(f"\nWord Bites stats:")
            print(f"Vertical words: {vertical_words_count}")
            print(f"Horizontal words: {horizontal_words_count}")
            print(f"Total score: {total_score}")
            break
        
        move = prioritized_move.move
        processed_count += 1
        
        # Only log every 5th word to reduce console output overhead
        if processed_count % 5 == 0 or processed_count == 1:
            orientation = "VERTICAL" if move.is_vertical else "HORIZONTAL"
            print(f"Playing word {processed_count}/{total_moves}: {move.word} ({move.score} pts) [{orientation}]")
        
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
                    modified_move = WordBitesMove(move.word, modified_block_moves, move.score, move.is_vertical, move.block_moves)
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
            time.sleep(0.01)  # Further reduced delay between words
            
            # Update stats
            if move.is_vertical:
                vertical_words_count += 1
            else:
                horizontal_words_count += 1
            total_score += move.score
        else:
            # If we fail to form a word, wait a bit before trying the next one
            time.sleep(0.01)  # Further reduced delay after failure
            # Reset last word tracking since we failed
            last_word = None
            last_word_blocks = {}

if __name__ == "__main__":
    main() 