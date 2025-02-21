from dataclasses import dataclass
from typing import List, Optional, Tuple, Set
from enum import Enum

class BlockType(Enum):
    SINGLE = "single"
    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"

@dataclass(frozen=True)
class Block:
    """Represents a single block in the Word Bites game"""
    type: BlockType
    letters: List[str]  # Will contain 1 or 2 letters depending on type
    position: Tuple[int, int]  # (row, col) coordinates of primary position
    
    def __post_init__(self):
        # Convert letters list to tuple to make it immutable
        object.__setattr__(self, 'letters', tuple(self.letters))
        
        # Validate block configuration
        if self.type == BlockType.SINGLE and len(self.letters) != 1:
            raise ValueError("Single blocks must have exactly one letter")
        if (self.type in [BlockType.VERTICAL, BlockType.HORIZONTAL] and 
            len(self.letters) != 2):
            raise ValueError("Vertical and horizontal blocks must have exactly two letters")
    
    def __hash__(self):
        return hash((self.type, self.letters, self.position))
    
    def get_all_positions(self) -> Set[Tuple[int, int]]:
        """Get all positions this block occupies"""
        positions = {self.position}
        row, col = self.position
        if self.type == BlockType.VERTICAL:
            positions.add((row + 1, col))
        elif self.type == BlockType.HORIZONTAL:
            positions.add((row, col + 1))
        return positions
    
    def move_to(self, new_row: int, new_col: int) -> 'Block':
        """Create a new block at the new position (since Block is immutable)"""
        return Block(
            type=self.type,
            letters=list(self.letters),  # Convert back to list for constructor
            position=(new_row, new_col)
        )

class WordBitesBoard:
    ROWS = 9  # 9 rows
    COLS = 8  # 8 columns
    
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
    
    def add_block(self, block: Block, combine: bool = True) -> bool:
        """
        Add a block to the board if the position is valid and empty.
        Args:
            block: The block to add
            combine: Whether to check for and combine touching blocks after adding
        Returns True if successful, False if position is invalid or occupied.
        """
        row, col = block.position
        
        if not self.is_valid_position(block, row, col):
            return False
            
        # Add block to all its positions
        for pos_row, pos_col in block.get_all_positions():
            self.grid[pos_row][pos_col] = block
            
        self.blocks.append(block)
        
        # After adding a block, optionally check for and combine touching blocks
        if combine:
            self.combine_touching_blocks()
        return True
    
    def combine_touching_blocks(self) -> None:
        """Combine single blocks that are touching into double blocks."""
        # Keep track of blocks we've already processed
        processed = set()
        new_blocks = []
        blocks_to_remove = []

        for block in self.blocks:
            if block in processed:
                continue

            row, col = block.position
            
            # Only try to combine single blocks
            if block.type != BlockType.SINGLE:
                new_blocks.append(block)
                processed.add(block)
                continue

            # Check right for horizontal connection
            right_block = self.get_block_at(row, col + 1)
            if (right_block and right_block.type == BlockType.SINGLE and 
                right_block not in processed):
                # Create horizontal double block
                new_block = Block(
                    type=BlockType.HORIZONTAL,
                    letters=[block.letters[0], right_block.letters[0]],
                    position=(row, col)
                )
                new_blocks.append(new_block)
                processed.add(block)
                processed.add(right_block)
                blocks_to_remove.extend([block, right_block])
                continue

            # Check below for vertical connection
            below_block = self.get_block_at(row + 1, col)
            if (below_block and below_block.type == BlockType.SINGLE and 
                below_block not in processed):
                # Create vertical double block
                new_block = Block(
                    type=BlockType.VERTICAL,
                    letters=[block.letters[0], below_block.letters[0]],
                    position=(row, col)
                )
                new_blocks.append(new_block)
                processed.add(block)
                processed.add(below_block)
                blocks_to_remove.extend([block, right_block])
                continue

            # If no connections found, keep as single block
            if block not in processed:
                new_blocks.append(block)
                processed.add(block)

        # Clear the board and add all blocks back
        self.blocks.clear()
        self.grid = [[None for _ in range(self.COLS)] for _ in range(self.ROWS)]
        
        # Add all the new blocks without combining (to prevent recursion)
        for block in new_blocks:
            if block not in blocks_to_remove:
                self.add_block(block, combine=False)

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
        self.blocks.remove(block)
            
        # Create new block at new position
        new_block = block.move_to(to_row, to_col)
        
        # Add to new positions
        new_positions = new_block.get_all_positions()
        for new_row, new_col in new_positions:
            self.grid[new_row][new_col] = new_block
        self.blocks.append(new_block)
            
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
    
    def get_blocks_list_str(self) -> str:
        """Return a string listing all blocks in a readable format."""
        if not self.blocks:
            return "No blocks on board"
            
        blocks_str = []
        for i, block in enumerate(self.blocks, 1):
            row, col = block.position
            letters_str = "".join(block.letters)
            blocks_str.append(f"{i}. {block.type.value} block '{letters_str}' at position ({row}, {col})")
        return "\n".join(blocks_str)

    def __str__(self) -> str:
        """Return a string representation of the board."""
        # First get the grid representation
        grid_str = []
        for row in range(self.ROWS):
            row_str = []
            for col in range(self.COLS):
                block = self.grid[row][col]
                if block and block.position == (row, col):  # Primary position
                    # Show connection for double blocks
                    if block.type == BlockType.HORIZONTAL:
                        row_str.append(f"[{block.letters[0]}-")  # First letter with horizontal connector
                    elif block.type == BlockType.VERTICAL:
                        row_str.append(f"[{block.letters[0]}|")  # First letter with vertical connector
                    else:
                        row_str.append(f"[{block.letters[0]}]")  # Single letter
                elif block and block.type == BlockType.HORIZONTAL and block.position[1] == col - 1:
                    # Second letter of horizontal stack
                    row_str.append(f"{block.letters[1]}]")  # Just the letter and closing bracket
                elif block and block.type == BlockType.VERTICAL and block.position[0] == row - 1:
                    # Second letter of vertical stack
                    row_str.append(f"[{block.letters[1]}]")  # Normal brackets for second vertical letter
                else:
                    row_str.append("[ ]")
            grid_str.append(" ".join(row_str))
            
        # Combine grid and blocks list
        return "\n".join([
            "Board Grid:",
            "\n".join(grid_str),
            "\nBlocks List:",
            self.get_blocks_list_str()
        ])
        
    def __iter__(self):
        """Make the board iterable, returning rows of letters."""
        for row in range(self.ROWS):
            current_row = []
            for col in range(self.COLS):
                block = self.grid[row][col]
                if block and block.position == (row, col):  # Primary position
                    current_row.append(block.letters[0])
                elif block and (
                    (block.type == BlockType.VERTICAL and block.position[0] == row - 1) or
                    (block.type == BlockType.HORIZONTAL and block.position[1] == col - 1)
                ):
                    # Second letter of either vertical or horizontal stack
                    current_row.append(block.letters[1])
                else:
                    current_row.append(" ")
            yield current_row

# Example usage:
if __name__ == "__main__":
    # Create a Word Bites board (9x8)
    board = WordBitesBoard()
    
    # Add blocks that should combine
    blocks = [
        Block(BlockType.SINGLE, ["S"], (0, 0)),
        Block(BlockType.SINGLE, ["T"], (0, 1)),  # Should combine with S horizontally
        Block(BlockType.SINGLE, ["A"], (2, 0)),
        Block(BlockType.SINGLE, ["B"], (3, 0)),  # Should combine with A vertically
        Block(BlockType.SINGLE, ["C"], (2, 2)),
        Block(BlockType.SINGLE, ["D"], (2, 3)),  # Should combine with C horizontally
        Block(BlockType.SINGLE, ["E"], (4, 4)),  # Should stay single
    ]
    
    for block in blocks:
        if not board.add_block(block):
            print(f"Failed to add block at position {block.position}")
        
    print("Word Bites board with combined blocks:")
    print(board) 