from get_game_board import get_game_board
from word_finder import find_words, print_found_words
from word_drawer import draw_all_words
from press_start_button import focus_and_click_start
import time
import signal
import sys
from concurrent.futures import ThreadPoolExecutor
import heapq
from dataclasses import dataclass
from typing import Tuple, List
import os
from threading import Lock

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
    print("\nTime's up! Exiting program...")
    os._exit(0)

def main():
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(90)
    
    try:
        # Focus window and click start
        if not focus_and_click_start():
            print("Failed to start game")
            return
            
        # Wait for game to start
        time.sleep(1)
        
        # Get the actual game board from screenshot
        board = get_game_board()
        
        if board:
            print("Game Board:")
            for row in board:
                print(' '.join(row))
            
            # Create a priority queue for found words
            word_queue = []  # Will be used as a heap
            word_paths = {}  # Store word->path mapping
            heap_lock = Lock()
            
            # Start a thread for drawing words
            with ThreadPoolExecutor(max_workers=1) as executor:
                # Submit the drawing task
                draw_future = executor.submit(draw_words_from_heap, word_queue, heap_lock)
                
                # Find and process words
                for word, path in find_words(board):
                    if word not in word_paths:  # Only process if not already found
                        word_paths[word] = path
                        with heap_lock:
                            heapq.heappush(word_queue, PrioritizedWord(word, path))
                
                # Signal that we're done finding words
                with heap_lock:
                    heapq.heappush(word_queue, PrioritizedWord("", []))  # Sentinel value
                
                # Wait for drawing to complete
                draw_future.result()
            
            # Print final results
            print_found_words(word_paths)
            
        else:
            print("Failed to get game board")
            
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
    finally:
        # Cancel the alarm in case we finish early
        signal.alarm(0)

def draw_words_from_heap(word_heap, heap_lock):
    """Draw words as they become available in the heap, longest first"""
    while True:
        with heap_lock:
            if not word_heap:
                time.sleep(0.1)  # Short sleep if heap is empty but still collecting words
                continue
            
            prioritized_word = heapq.heappop(word_heap)
        
        # Check for sentinel value
        if not prioritized_word.path:  # Empty path means sentinel
            break
            
        # Convert single word-path pair to dictionary format
        words_dict = {prioritized_word.word: prioritized_word.path}
        draw_all_words(words_dict)  # Draw single word

if __name__ == "__main__":
    main() 