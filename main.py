from get_game_board import get_game_board
from identify_game_version import identify_game_version
from word_finder import find_words, find_anagrams, print_found_words, print_anagram_words
from word_drawer import draw_word, click_anagram_word
from press_start_button import focus_and_click_start
import time
import signal
from concurrent.futures import ThreadPoolExecutor
import heapq
from dataclasses import dataclass
from typing import Tuple, List
import os
from threading import Lock

WORDS_FOUND = 0
GAME_VERSION = "unknown"
TIME_REMAINING = 80  # Track time remaining
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

def timeout_handler(signum, frame):
    print("\nTime's up! Game summary:")
    print("------------------------")
    print(f"Game version: {GAME_VERSION}")
    print(f"Words found: {WORDS_FOUND}")
    print(f"Time played: 80 seconds")
    print("Program terminated.")
    os._exit(0)

def update_time_remaining():
    global TIME_REMAINING
    TIME_REMAINING = max(0, 80 - (time.time() - START_TIME))

def main():
    try:
        global START_TIME
        START_TIME = time.time()
        words_found = 0
        
        # Focus window and click start
        if not focus_and_click_start():
            print("Failed to start game")
            return
            
        # Wait for game to start
        time.sleep(1)
        
        # Start the 80-second timer
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(80)
        
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
            for row in board:
                print(' '.join(row))

            # Handle differently based on game type
            if game_version.startswith('ANAGRAM'):
                # For anagrams, find words and click them one by one
                found_words = find_anagrams(board, min_length=3)
                words_found = len(found_words)
                
                # Sort words by length (longest first) and alphabetically
                sorted_words = sorted(found_words.keys(), key=lambda x: (-len(x), x))
                
                # Click each word
                for word in sorted_words:
                    click_anagram_word(word, board, game_version)
                    time.sleep(0.1)  # Small delay between words
                
                print_anagram_words(found_words)
            else:
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

if __name__ == "__main__":
    main() 