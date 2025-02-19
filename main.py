from get_game_board import get_game_board
from word_finder import find_words, print_found_words
from word_drawer import draw_all_words
import time
import signal
import sys

def timeout_handler(signum, frame):
    print("\nTime's up! Exiting program...")
    sys.exit(0)

def main():
    # Set 2 minute timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(90)  # 120 seconds = 2 minutes
    
    try:
        # Get the actual game board from screenshot
        board = get_game_board()
        
        if board:
            print("Game Board:")
            for row in board:
                print(' '.join(row))
            
            # Find all possible words
            found_words = find_words(board)
            
            # Print results
            print_found_words(found_words)
            
            # Draw all words automatically
            draw_all_words(found_words)
            
        else:
            print("Failed to get game board")
            
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
    finally:
        # Cancel the alarm in case we finish early
        signal.alarm(0)

if __name__ == "__main__":
    main() 