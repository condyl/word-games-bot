#!/usr/bin/env python3

import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from word_finder import WordBitesMove
from word_drawer import execute_word_bites_moves
from word_bites_board import WordBitesBoard, Block, BlockType

# Create a mock board for testing
class MockBoard(WordBitesBoard):
    def __init__(self):
        self.ROWS = 9
        self.COLS = 8
        self.blocks = []
        self.moves_log = []
        self.letter_to_blocks = {}  # Add this attribute for compatibility
        
        # Add some blocks to the board
        self.add_block(Block(BlockType.SINGLE, ['I'], (0, 0)))
        self.add_block(Block(BlockType.SINGLE, ['C'], (0, 1)))
        self.add_block(Block(BlockType.SINGLE, ['E'], (0, 2)))
        self.add_block(Block(BlockType.SINGLE, ['W'], (0, 3)))
        self.add_block(Block(BlockType.HORIZONTAL, ['O', 'R'], (0, 4)))
        self.add_block(Block(BlockType.SINGLE, ['M'], (0, 6)))
        self.add_block(Block(BlockType.SINGLE, ['S'], (0, 7)))
        
    def add_block(self, block):
        self.blocks.append(block)
        # Update letter_to_blocks index
        for letter in block.letters:
            if letter not in self.letter_to_blocks:
                self.letter_to_blocks[letter] = []
            self.letter_to_blocks[letter].append(block)
    
    def get_block_at(self, row, col):
        for block in self.blocks:
            if block.position == (row, col):
                return block
            # Check second position for horizontal/vertical blocks
            if block.type == BlockType.HORIZONTAL and block.position == (row, col-1):
                return block
            if block.type == BlockType.VERTICAL and block.position == (row-1, col):
                return block
        return None
    
    def get_blocks_by_letter(self, letter):
        """Get all blocks containing the specified letter."""
        return self.letter_to_blocks.get(letter, [])
    
    def __str__(self):
        return f"Mock Board with {len(self.blocks)} blocks"

# Override the move_word_bites_block function to log moves instead of actually moving blocks
def mock_move_word_bites_block(block, row, col, board):
    print(f"MOCK: Moving block {block.letters} from {block.position} to ({row}, {col})")
    
    # Update the block's position
    old_position = block.position
    block_index = board.blocks.index(block)
    
    # Create a new block with the updated position (since blocks are immutable)
    new_block = Block(block.type, list(block.letters), (row, col))
    board.blocks[block_index] = new_block
    
    # Log the move
    if isinstance(board, MockBoard):
        board.moves_log.append((block.letters, old_position, (row, col)))
    
    return True

# Patch the move_word_bites_block function
import word_drawer
word_drawer.move_word_bites_block = mock_move_word_bites_block

def main():
    # Create a mock board
    board = MockBoard()
    
    # Create moves for "ICEWORM" and "ICEWORMS"
    iceworm_blocks = [
        (Block(BlockType.SINGLE, ['I'], (0, 0)), (3, 0)),
        (Block(BlockType.SINGLE, ['C'], (0, 1)), (3, 1)),
        (Block(BlockType.SINGLE, ['E'], (0, 2)), (3, 2)),
        (Block(BlockType.SINGLE, ['W'], (0, 3)), (3, 3)),
        (Block(BlockType.HORIZONTAL, ['O', 'R'], (0, 4)), (3, 4)),
        (Block(BlockType.SINGLE, ['M'], (0, 6)), (3, 6))
    ]
    
    iceworms_blocks = [
        (Block(BlockType.SINGLE, ['I'], (0, 0)), (3, 0)),
        (Block(BlockType.SINGLE, ['C'], (0, 1)), (3, 1)),
        (Block(BlockType.SINGLE, ['E'], (0, 2)), (3, 2)),
        (Block(BlockType.SINGLE, ['W'], (0, 3)), (3, 3)),
        (Block(BlockType.HORIZONTAL, ['O', 'R'], (0, 4)), (3, 4)),
        (Block(BlockType.SINGLE, ['M'], (0, 6)), (3, 6)),
        (Block(BlockType.SINGLE, ['S'], (0, 7)), (3, 7))
    ]
    
    move1 = WordBitesMove("ICEWORM", iceworm_blocks, 2000)
    move2 = WordBitesMove("ICEWORMS", iceworms_blocks, 2400)
    
    # Execute the moves
    print("Testing word extension functionality...")
    print("Executing moves for 'ICEWORM' and 'ICEWORMS'")
    execute_word_bites_moves([move1, move2], board)
    
    # Check the moves log to see if the second word reused the first word's blocks
    print("\nMove log:")
    for i, (letters, from_pos, to_pos) in enumerate(board.moves_log):
        print(f"{i+1}. Moved {letters} from {from_pos} to {to_pos}")
    
    # Count how many blocks were moved for each word
    iceworm_moves = 0
    iceworms_moves = 0
    in_second_word = False
    
    # Print the full log to debug
    print("\nFull log:")
    for i, entry in enumerate(board.moves_log):
        print(f"{i+1}. {entry}")
    
    # Count moves for each word
    for letters, from_pos, to_pos in board.moves_log:
        if not in_second_word and from_pos[0] == 0:  # First word moves blocks from row 0
            iceworm_moves += 1
        elif in_second_word:
            iceworms_moves += 1
        
        # Check if we've completed the first word
        if letters == ('M',) and to_pos == (3, 6):
            in_second_word = True
    
    print(f"\nBlocks moved for 'ICEWORM': {iceworm_moves}")
    print(f"Blocks moved for 'ICEWORMS': {iceworms_moves}")
    
    if iceworms_moves == 1:
        print("\nSUCCESS: Only the 'S' block was moved to form 'ICEWORMS'!")
    else:
        print("\nFAILURE: More than one block was moved to form 'ICEWORMS'.")

if __name__ == "__main__":
    main() 