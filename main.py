from get_game_board import get_game_board
from word_finder import find_words, print_found_words

def main():
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
    else:
        print("Failed to get game board")

if __name__ == "__main__":
    main() 