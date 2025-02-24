import time
from typing import List, Tuple
import Quartz
from word_bites_board import WordBitesBoard, Block, BlockType
from word_finder import WordBitesMove

def get_iphone_window():
    """Get the iPhone mirroring window position and dimensions."""
    # Get all windows
    windows = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
        Quartz.kCGNullWindowID
    )
    
    # Find iPhone window
    for window in windows:
        name = window.get(Quartz.kCGWindowName, '')
        if name and "iPhone" in name:
            bounds = window.get(Quartz.kCGWindowBounds)
            return {
                'x': bounds['X'],
                'y': bounds['Y'],
                'width': bounds['Width'],
                'height': bounds['Height']
            }
    return None

def get_letter_position(x: int, y: int, game_version: str = "4x4") -> Tuple[int, int]:
    """
    Convert board coordinates to screen coordinates.
    Note: Input coordinates are (row, col) format
    """
    window = get_iphone_window()
    if not window:
        raise Exception("iPhone window not found")
    
    # Match the exact region calculation from get_game_board.py
    width = window['width']
    height = window['height']
    
    # Use the exact same margins as get_game_board.py
    if game_version == "4x4":
        start_y = int(height * 0.47)
        end_y = int(height * 0.79)
        start_x = int(width * 0.11)
        end_x = int(width * 0.89)
    else:  # "X", "O", "5x5"
        start_y = int(height * 0.44)
        end_y = int(height * 0.82)
        start_x = int(width * 0.06)
        end_x = int(width * 0.94)
    
    # Calculate board dimensions
    board_width = end_x - start_x
    board_height = end_y - start_y
    
    # Determine grid size based on game version
    board_size = 4 if game_version == "4x4" else 5
    
    # Calculate cell size
    cell_width = board_width / board_size
    cell_height = board_height / board_size
    
    # Swap x and y to match the grid orientation
    # y coordinate determines horizontal position (column)
    # x coordinate determines vertical position (row)
    screen_x = window['x'] + start_x + (cell_width * y) + (cell_width / 2)
    screen_y = window['y'] + start_y + (cell_height * x) + (cell_height / 2)
    
    return (int(screen_x), int(screen_y))

def get_anagram_letter_position(x: int, y: int, game_version: str) -> Tuple[int, int]:
    """
    Convert anagram board coordinates to screen coordinates.
    Note: Input coordinates are (row, col) format
    """
    window = get_iphone_window()
    if not window:
        raise Exception("iPhone window not found")
    
    width = window['width']
    height = window['height']
    
    # Use the exact same margins as get_game_board.py for anagrams
    if game_version == "ANAGRAM6":
        start_y = int(height * 0.80)
        end_y = int(height * 0.85)
        start_x = int(width * 0.03)
        end_x = int(width * 0.97)
    else:  # ANAGRAM7
        start_y = int(height * 0.80)
        end_y = int(height * 0.845)
        start_x = int(width * 0.02)
        end_x = int(width * 0.98)
    
    # Calculate board dimensions
    board_width = end_x - start_x
    board_height = end_y - start_y
    
    # Determine number of letters
    num_letters = 6 if game_version == "ANAGRAM6" else 7
    
    # Calculate letter spacing
    letter_width = board_width / num_letters
    
    # For anagrams, we only use the y coordinate as the letter index
    # x coordinate is always 0 since it's a single row
    screen_x = window['x'] + start_x + (letter_width * y) + (letter_width / 2)
    screen_y = window['y'] + start_y + (board_height / 2)
    
    return (int(screen_x), int(screen_y))

def get_word_bites_position(row: int, col: int) -> Tuple[int, int]:
    """
    Convert Word Bites board coordinates to screen coordinates.
    Note: Input coordinates are (row, col) format
    """
    window = get_iphone_window()
    if not window:
        raise Exception("iPhone window not found")
    
    width = window['width']
    height = window['height']
    
    # Use the exact same margins as get_game_board.py for Word Bites
    start_y = int(height * 0.36)
    end_y = int(height * 0.85)
    start_x = int(width * 0.02)  # Add small left margin
    end_x = int(width * 0.98)    # Add small right margin
    
    # Calculate board dimensions
    board_width = end_x - start_x
    board_height = end_y - start_y
    
    # Calculate cell size
    cell_width = board_width / WordBitesBoard.COLS
    cell_height = board_height / WordBitesBoard.ROWS
    
    # Calculate screen coordinates with margins
    screen_x = window['x'] + start_x + (cell_width * col) + (cell_width / 2)
    screen_y = window['y'] + start_y + (cell_height * row) + (cell_height / 2)
    
    # Ensure we don't go beyond the right edge
    max_x = window['x'] + end_x - (cell_width / 4)
    screen_x = min(screen_x, max_x)
    
    return (int(screen_x), int(screen_y))

def move_word_bites_block(block: Block, target_row: int, target_col: int, board: WordBitesBoard) -> bool:
    """
    Move a Word Bites block from its current position to a target position.
    Returns True if successful, False otherwise.
    """
    from_row, from_col = block.position
    
    try:
        # Verify the block is actually at its expected position
        actual_block = board.get_block_at(from_row, from_col)
        if actual_block != block:
            return False
        
        # For vertical blocks, ensure we're using the top position for both source and target
        if block.type == BlockType.VERTICAL:
            if target_row + 1 >= board.ROWS:
                target_row -= 1
            if not (0 <= target_row + 1 < board.ROWS):
                return False
            for r in [target_row, target_row + 1]:
                existing = board.get_block_at(r, target_col)
                if existing and existing != block:
                    return False
        elif block.type == BlockType.HORIZONTAL:
            if target_col + 1 >= board.COLS:
                target_col -= 1
            if not (0 <= target_col + 1 < board.COLS):
                return False
            for c in [target_col, target_col + 1]:
                existing = board.get_block_at(target_row, c)
                if existing and existing != block:
                    return False
        
        # Get screen coordinates
        start_x, start_y = get_word_bites_position(from_row, from_col)
        end_x, end_y = get_word_bites_position(target_row, target_col)
        
        # Calculate distance for drag
        distance = ((end_x - start_x) ** 2 + (end_y - start_y) ** 2) ** 0.5
        
        # Move mouse to block
        move = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, (start_x, start_y), 0)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, move)
        time.sleep(0.1)
        
        # Click and hold
        down = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, (start_x, start_y), 0)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
        time.sleep(0.1)
        
        # For longer drags, use just 2-3 intermediate points
        if distance > 150:
            num_steps = 2
            for i in range(1, num_steps + 1):
                intermediate_x = start_x + (end_x - start_x) * (i / (num_steps + 1))
                intermediate_y = start_y + (end_y - start_y) * (i / (num_steps + 1))
                drag = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDragged, 
                                                    (intermediate_x, intermediate_y), 0)
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, drag)
                time.sleep(0.1)
        
        # Final drag to target
        drag = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDragged, (end_x, end_y), 0)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, drag)
        time.sleep(0.1)
        
        # Release
        up = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, (end_x, end_y), 0)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
        time.sleep(0.1)
        
        # Verify the move was successful
        success = board.move_block(from_row, from_col, target_row, target_col)
        if not success:
            # One quick retry with slightly longer delays
            time.sleep(0.2)
            move = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, (start_x, start_y), 0)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, move)
            time.sleep(0.2)
            down = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, (start_x, start_y), 0)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
            time.sleep(0.2)
            drag = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDragged, (end_x, end_y), 0)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, drag)
            time.sleep(0.2)
            up = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, (end_x, end_y), 0)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
            time.sleep(0.2)
            success = board.move_block(from_row, from_col, target_row, target_col)
        
        return success
        
    except Exception as e:
        print(f"Error moving block: {str(e)}")
        return False

def execute_word_bites_move(move: WordBitesMove, board: WordBitesBoard) -> bool:
    """
    Execute a Word Bites move by moving all required blocks into position.
    Returns True if all blocks were moved successfully.
    """
    print("\nInitial board state:")
    print(board)
    
    # Track all blocks and their positions for restoration
    original_positions = {}
    for block in board.blocks:
        original_positions[block] = block.position
    
    # First, identify all positions we need for the word
    word_positions = set()
    blocks_needed = {}  # Map target position -> block needed there
    
    for block, target_pos in move.block_moves:
        row, col = target_pos
        word_positions.add((row, col))
        blocks_needed[target_pos] = block
        # Add second position for double blocks
        if block.type == BlockType.HORIZONTAL:
            word_positions.add((row, col + 1))
        elif block.type == BlockType.VERTICAL:
            word_positions.add((row + 1, col))
    
    # Find blocks that are in the way
    blocks_to_clear = set()  # Use a set to avoid duplicates
    for pos in word_positions:
        row, col = pos
        block = board.get_block_at(row, col)
        if block:
            # If this block is needed but not in the right position, clear it
            is_needed = False
            correct_position = False
            for needed_pos, needed_block in blocks_needed.items():
                if block == needed_block:
                    is_needed = True
                    if block.position == needed_pos:
                        correct_position = True
                    break
            
            if not is_needed or (is_needed and not correct_position):
                blocks_to_clear.add(block)  # Using set to avoid duplicates
    
    # Sort blocks to clear by position (bottom-to-top, right-to-left)
    blocks_to_clear = sorted(blocks_to_clear, key=lambda b: (-b.position[0], -b.position[1]))
    
    # Track temporary positions of cleared blocks
    temp_positions = {}  # Map block -> temporary position
    
    # Move blocking blocks to temporary positions
    for block in blocks_to_clear:
        print(f"\nClearing block {block.letters} from position {block.position}")
        orig_pos = block.position
        
        # Find a free position that won't interfere with word formation
        temp_pos = None
        # Start from the bottom of the board
        for r in range(board.ROWS - 1, -1, -1):
            for c in range(board.COLS - 1, -1, -1):
                # Skip positions needed for the word
                if (r, c) in word_positions:
                    continue
                    
                # Check space requirements for the block
                positions_needed = {(r, c)}
                if block.type == BlockType.HORIZONTAL:
                    if c + 1 >= board.COLS:
                        continue
                    if (r, c + 1) in word_positions:
                        continue
                    positions_needed.add((r, c + 1))
                elif block.type == BlockType.VERTICAL:
                    if r + 1 >= board.ROWS:
                        continue
                    if (r + 1, c) in word_positions:
                        continue
                    positions_needed.add((r + 1, c))
                
                # Check if all needed positions are free
                can_place = True
                for pos_r, pos_c in positions_needed:
                    if not (0 <= pos_r < board.ROWS and 0 <= pos_c < board.COLS):
                        can_place = False
                        break
                    existing_block = board.get_block_at(pos_r, pos_c)
                    if existing_block and existing_block != block:
                        can_place = False
                        break
                
                if can_place:
                    temp_pos = (r, c)
                    break
            if temp_pos:
                break
        
        if temp_pos:
            print(f"Moving block {block.letters} to temporary position {temp_pos}")
            if move_word_bites_block(block, temp_pos[0], temp_pos[1], board):
                temp_positions[block] = orig_pos
                print("\nBoard after clearing move:")
                print(board)
                time.sleep(0.3)
            else:
                print(f"Failed to move blocking block {block.letters} to temporary position {temp_pos}")
                restore_blocks(original_positions, board)
                return False
        else:
            print(f"Could not find temporary position for blocking block {block.letters}")
            restore_blocks(original_positions, board)
            return False
    
    # Sort moves by position (top-to-bottom, left-to-right)
    sorted_moves = sorted(move.block_moves, key=lambda x: (x[1][0], x[1][1]))
    
    # Move each block to its target position
    success = True
    for i, (block, target_pos) in enumerate(sorted_moves):
        print(f"\nPlacing letter {i+1} of {len(move.block_moves)}: {block.letters} to position {target_pos}")
        
        # Skip if block is already in correct position
        if block.position == target_pos:
            print(f"Block {block.letters} is already in position {target_pos}")
            continue
        
        # Try to move the block
        attempts = 0
        while attempts < 3:
            if move_word_bites_block(block, target_pos[0], target_pos[1], board):
                print("\nBoard after placing letter:")
                print(board)
                time.sleep(0.3)
                break
            print(f"Attempt {attempts + 1} failed, retrying...")
            attempts += 1
            time.sleep(0.3)
        
        if attempts == 3:
            print(f"Failed to move block {block.letters} to position {target_pos}")
            success = False
            break
    
    # If we failed, restore all blocks to their original positions
    if not success:
        print("\nMove failed, attempting to restore original positions...")
        restore_blocks(original_positions, board)
    
    print("\nFinal board state:")
    print(board)
    return success

def restore_blocks(original_positions: dict, board: WordBitesBoard) -> None:
    """Helper function to restore blocks to their original positions"""
    # Sort blocks by position (bottom-to-top, right-to-left)
    blocks_to_restore = sorted(original_positions.items(), 
                             key=lambda x: (-x[1][0], -x[1][1]))
    
    for block, orig_pos in blocks_to_restore:
        if block.position == orig_pos:
            continue  # Skip if already in correct position
            
        print(f"\nRestoring block {block.letters} to position {orig_pos}")
        attempts = 0
        while attempts < 3:  # Try up to 3 times
            if move_word_bites_block(block, orig_pos[0], orig_pos[1], board):
                print("\nBoard after restoring block:")
                print(board)
                time.sleep(0.2)  # Longer delay between moves
                break
            print(f"Attempt {attempts + 1} failed, retrying...")
            attempts += 1
            time.sleep(0.3)  # Longer delay between attempts
        if attempts == 3:
            print(f"Warning: Failed to restore block {block.letters} to position {orig_pos} after 3 attempts")

def execute_word_bites_moves(moves: List[WordBitesMove], board: WordBitesBoard) -> None:
    """
    Execute a list of Word Bites moves in order (highest scoring first).
    """
    for move in moves:
        print(f"\nForming word '{move.word}' ({move.score} points)")
        if execute_word_bites_move(move, board):
            print(f"Successfully formed word '{move.word}'")
            time.sleep(0.5)  # Wait between words
        else:
            print(f"Failed to form word '{move.word}'")
            break

def draw_word(path: List[Tuple[int, int]], game_version: str = "4x4"):
    """Draw a word by dragging the mouse through the given path."""
    if not path:
        return
    
    start_x, start_y = get_letter_position(path[0][0], path[0][1], game_version)
    
    try:
        move = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, (start_x, start_y), 0)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, move)
        
        down = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, (start_x, start_y), 0)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
        
        for i, (x, y) in enumerate(path[1:], 1):
            screen_x, screen_y = get_letter_position(x, y, game_version)
            drag = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDragged, (screen_x, screen_y), 0)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, drag)
            time.sleep(0.02)  # Minimum reliable delay
            
    finally:
        # Release at end
        up = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, (screen_x, screen_y), 0)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
        time.sleep(0.02)  # Minimum reliable delay

def draw_all_words(words: dict[str, List[Tuple[int, int]]], game_version: str = "4x4"):
    """
    Draw all words in the found_words dictionary.
    Draws longer words first (they're worth more points).
    """
    # Sort words by length (longest first) and alphabetically
    sorted_words = sorted(words.items(), key=lambda x: (-len(x[0]), x[0]))
    
    for word, path in sorted_words:
        draw_word(path, game_version)

def click_anagram_word(word: str, board: List[List[str]], game_version: str):
    """
    Click letters to spell out an anagram word, then click enter.
    Args:
        word: The word to enter
        board: Single-row grid of letters from get_game_board
        game_version: "ANAGRAM6" or "ANAGRAM7"
    """
    if not word:
        return
    
    window = get_iphone_window()
    if not window:
        raise Exception("iPhone window not found")
    
    # Enter button position as percentage of window dimensions
    enter_x_percent = 0.50  # Center horizontally
    enter_y_percent = 0.60  # Near bottom of screen
    
    # Calculate actual coordinates
    enter_x = window['x'] + (window['width'] * enter_x_percent)
    enter_y = window['y'] + (window['height'] * enter_y_percent)
    
    try:
        # Get the letters in the board and track used positions
        available_letters = list(board[0])  # Convert to list to track used positions
        used_positions = set()
        
        # Click each letter in the word
        for letter in word:
            letter = letter.upper()
            # Find position of this letter, skipping already used positions
            letter_pos = -1
            for i, board_letter in enumerate(available_letters):
                if board_letter == letter and i not in used_positions:
                    letter_pos = i
                    used_positions.add(i)
                    break
                    
            if letter_pos == -1:
                print(f"Warning: Letter '{letter}' not found in remaining letters {[l for i,l in enumerate(available_letters) if i not in used_positions]}")
                continue
            
            # Get screen coordinates for this letter
            x, y = get_anagram_letter_position(0, letter_pos, game_version)
            
            # Move to letter position
            move = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, (x, y), 0)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, move)
            
            # Click down
            down = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, (x, y), 0)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
            
            # Click up
            up = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, (x, y), 0)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
            
            time.sleep(0.02)  # Small delay between clicks
        
        # Click enter button
        # Move to enter button
        move = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, (enter_x, enter_y), 0)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, move)
        
        # Click down
        down = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, (enter_x, enter_y), 0)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
        
        # Click up
        up = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, (enter_x, enter_y), 0)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
        
        time.sleep(0.02)  # Small delay after enter
        
    except Exception as e:
        print(f"Error clicking anagram word: {str(e)}")