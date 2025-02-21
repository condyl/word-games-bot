from dataclasses import dataclass
from typing import List, Optional, Tuple, Set
from enum import Enum

class BlockType(Enum):
    SINGLE = "single"
    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"

@dataclass
class Block:
    """Represents a single block in the Word Bites game"""
    type: BlockType
    letters: List[str]  # Will contain 1 or 2 letters depending on type
    position: Tuple[int, int]  # (row, col) coordinates of primary position
    
    def __post_init__(self):
        # Validate block configuration
        if self.type == BlockType.SINGLE and len(self.letters) != 1:
            raise ValueError("Single blocks must have exactly one letter")
        if (self.type in [BlockType.VERTICAL, BlockType.HORIZONTAL] and 
            len(self.letters) != 2):
            raise ValueError("Vertical and horizontal blocks must have exactly two letters")
    
    def get_all_positions(self) -> Set[Tuple[int, int]]:
        """Get all positions this block occupies"""
        positions = {self.position}
        row, col = self.position
        if self.type == BlockType.VERTICAL:
            positions.add((row + 1, col))
        elif self.type == BlockType.HORIZONTAL:
            positions.add((row, col + 1))
        return positions
    
    def move_to(self, new_row: int, new_col: int) -> None:
        """Move the block to a new position"""
        self.position = (new_row, new_col)

class WordBitesBoard:
    ROWS = 8
    COLS = 9
    
    def __init__(self):
        self.blocks: List[Block] = []
        # We'll maintain a grid of references to blocks for easy position-based lookup
        self.grid: List[List[Optional[Block]]] = [[None for _ in range(self.COLS)] for _ in range(self.ROWS)]
    
    def is_valid_position(self, block: Block, row: int, col: int) -> bool:
        """Check if a block can be placed at the given position"""
        if not (0 <= row < self.ROWS and 0 <= col < self.COLS):
            return False
            
        # Check all positions the block would occupy
        if block.type == BlockType.VERTICAL:
            if row + 1 >= self.ROWS:
                return False
            return (self.grid[row][col] is None and 
                   self.grid[row + 1][col] is None)
        elif block.type == BlockType.HORIZONTAL:
            if col + 1 >= self.COLS:
                return False
            return (self.grid[row][col] is None and 
                   self.grid[row][col + 1] is None)
        else:  # SINGLE
            return self.grid[row][col] is None
    
    def add_block(self, block: Block) -> bool:
        """
        Add a block to the board if the position is valid and empty.
        Returns True if successful, False if position is invalid or occupied.
        """
        row, col = block.position
        
        if not self.is_valid_position(block, row, col):
            return False
            
        # Add block to all its positions
        for pos_row, pos_col in block.get_all_positions():
            self.grid[pos_row][pos_col] = block
            
        self.blocks.append(block)
        return True
    
    def get_block_at(self, row: int, col: int) -> Optional[Block]:
        """Get the block at the specified position, if any."""
        if 0 <= row < self.ROWS and 0 <= col < self.COLS:
            return self.grid[row][col]
        return None
    
    def move_block(self, from_row: int, from_col: int, to_row: int, to_col: int) -> bool:
        """
        Move a block from one position to another.
        Returns True if successful, False if move is invalid.
        """
        block = self.get_block_at(from_row, from_col)
        if not block or block.position != (from_row, from_col):  # Only move from primary position
            return False
            
        # Check if new position is valid
        if not self.is_valid_position(block, to_row, to_col):
            return False
            
        # Remove from old positions
        old_positions = block.get_all_positions()
        for old_row, old_col in old_positions:
            self.grid[old_row][old_col] = None
            
        # Move block
        block.move_to(to_row, to_col)
        
        # Add to new positions
        new_positions = block.get_all_positions()
        for new_row, new_col in new_positions:
            self.grid[new_row][new_col] = block
            
        return True
    
    def remove_block(self, row: int, col: int) -> bool:
        """Remove a block from the specified position."""
        block = self.get_block_at(row, col)
        if not block:
            return False
            
        # Remove from all positions
        for pos_row, pos_col in block.get_all_positions():
            self.grid[pos_row][pos_col] = None
            
        self.blocks.remove(block)
        return True
    
    def __str__(self) -> str:
        """Return a string representation of the board."""
        result = []
        for row in range(self.ROWS):
            row_str = []
            for col in range(self.COLS):
                block = self.grid[row][col]
                if block and block.position == (row, col):  # Primary position
                    row_str.append(f"[{block.letters[0]}]")
                elif block and (
                    (block.type == BlockType.VERTICAL and block.position[0] == row - 1) or
                    (block.type == BlockType.HORIZONTAL and block.position[1] == col - 1)
                ):
                    # Second letter of either vertical or horizontal stack
                    row_str.append(f"[{block.letters[1]}]")
                else:
                    row_str.append("[ ]")
            result.append(" ".join(row_str))
        return "\n".join(result)

# Example usage:
if __name__ == "__main__":
    # Create a Word Bites board (8x9)
    board = WordBitesBoard()
    
    # Add some example blocks in a more realistic Word Bites layout
    blocks = [
        Block(BlockType.SINGLE, ["E"], (0, 4)),
        Block(BlockType.VERTICAL, ["S", "T"], (1, 2)),
        Block(BlockType.VERTICAL, ["I", "N"], (3, 4)),  # Changed to vertical to show both types
        Block(BlockType.SINGLE, ["G"], (3, 6)),
        Block(BlockType.HORIZONTAL, ["R", "A"], (4, 1)),
        Block(BlockType.VERTICAL, ["L", "Y"], (5, 3)),
        Block(BlockType.SINGLE, ["U"], (6, 5)),
        Block(BlockType.HORIZONTAL, ["E", "D"], (7, 2))
    ]
    
    for block in blocks:
        if not board.add_block(block):
            print(f"Failed to add block at position {block.position}")
        
    print("Initial Word Bites board (8x9):")
    print(board)
    
    print("\nMoving S-T block to position (2,3):")
    board.move_block(1, 2, 2, 3)
    print(board) 