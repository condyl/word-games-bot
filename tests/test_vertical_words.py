import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from word_finder import WordBitesMove, find_word_bites_words
from word_bites_board import WordBitesBoard, Block, BlockType

def test_vertical_word_finding():
    """Test that the bot can find vertical words (top to bottom)"""
    print("Testing vertical word finding functionality...")
    
    # Create a test board
    board = WordBitesBoard()
    
    # Add blocks to form a vertical word "TEST"
    board.add_block(Block(BlockType.SINGLE, ["T"], (0, 3)))
    board.add_block(Block(BlockType.SINGLE, ["E"], (1, 3)))
    board.add_block(Block(BlockType.SINGLE, ["S"], (2, 3)))
    board.add_block(Block(BlockType.SINGLE, ["T"], (3, 3)))
    
    # Add some other blocks for horizontal words
    board.add_block(Block(BlockType.SINGLE, ["C"], (4, 0)))
    board.add_block(Block(BlockType.SINGLE, ["A"], (4, 1)))
    board.add_block(Block(BlockType.SINGLE, ["T"], (4, 2)))
    
    # Find all possible words
    moves = find_word_bites_words(board, min_length=3)
    
    # Print the board
    print("Board:")
    print(board)
    
    # Print all found words
    print("\nFound words:")
    for move in moves:
        print(f"{move.word} ({move.score} points)")
        # Print if it's a vertical or horizontal word
        is_vertical = all(pos[1] == move.block_moves[0][1][1] for _, pos in move.block_moves)
        is_horizontal = all(pos[0] == move.block_moves[0][1][0] for _, pos in move.block_moves)
        if is_vertical:
            print("  (Vertical word)")
        elif is_horizontal:
            print("  (Horizontal word)")
    
    # Check if "TEST" was found (vertical word)
    test_found = any(move.word == "TEST" for move in moves)
    if test_found:
        print("\nSUCCESS: Vertical word 'TEST' was found!")
    else:
        print("\nFAILURE: Vertical word 'TEST' was not found!")
    
    # Check if "CAT" was found (horizontal word)
    cat_found = any(move.word == "CAT" for move in moves)
    if cat_found:
        print("SUCCESS: Horizontal word 'CAT' was found!")
    else:
        print("FAILURE: Horizontal word 'CAT' was not found!")
    
    return test_found and cat_found

if __name__ == "__main__":
    test_vertical_word_finding() 