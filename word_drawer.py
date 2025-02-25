import time
from typing import List, Tuple
import Quartz
from word_bites_board import WordBitesBoard, Block, BlockType
from word_finder import WordBitesMove, are_words_related

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
    Note: Input coordinates are (row, col) format where:
    - row: vertical position (0 at top, increasing downward)
    - col: horizontal position (0 at left, increasing rightward)
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
    # row determines Y position, col determines X position
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
            # Try to find the block's actual position on the board
            found = False
            for r in range(board.ROWS):
                for c in range(board.COLS):
                    check_block = board.get_block_at(r, c)
                    if check_block and check_block.letters == block.letters and check_block.type == block.type:
                        # Since Block is immutable, we need to use the actual block from the board
                        block = check_block
                        from_row, from_col = r, c
                        found = True
                        break
                if found:
                    break
            
            if not found:
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
        
        # Determine number of steps based on distance - fewer steps for speed
        num_steps = 0
        if distance > 300:  # Only use intermediate points for very long drags
            num_steps = 1
        
        # Try the move up to 2 times
        for attempt in range(2):
            try:
                # Move mouse to block
                move = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, (start_x, start_y), 0)
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, move)
                time.sleep(0.005)  # Further reduced delay
                
                # Click and hold
                down = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, (start_x, start_y), 0)
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
                time.sleep(0.005)  # Further reduced delay
                
                # Use intermediate points only for longer drags
                if num_steps > 0:
                    # Just use a single intermediate point at the midpoint
                    intermediate_x = start_x + (end_x - start_x) * 0.5
                    intermediate_y = start_y + (end_y - start_y) * 0.5
                    drag = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDragged, 
                                                        (intermediate_x, intermediate_y), 0)
                    Quartz.CGEventPost(Quartz.kCGHIDEventTap, drag)
                    time.sleep(0.005)  # Further reduced delay
                
                # Final drag to target
                drag = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDragged, (end_x, end_y), 0)
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, drag)
                time.sleep(0.005)  # Further reduced delay
                
                # Release
                up = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, (end_x, end_y), 0)
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
                time.sleep(0.01)  # Further reduced delay after release
                
                # Verify the move was successful
                success = board.move_block(from_row, from_col, target_row, target_col)
                if success:
                    return True
                
                # If we're on the last attempt, try a slightly different approach
                if attempt == 1:
                    # Try with slightly adjusted coordinates
                    start_x += 3
                    start_y += 3
                    end_x += 3
                    end_y += 3
                
                # Wait between attempts
                time.sleep(0.03)  # Further reduced delay
                
            except Exception as e:
                time.sleep(0.03)  # Further reduced delay
        
        return False
        
    except Exception as e:
        return False

def execute_word_bites_move(move: WordBitesMove, board: WordBitesBoard, preserve_word: bool = False) -> bool:
    """
    Execute a Word Bites move by moving all required blocks into position.
    Args:
        move: The move to execute
        board: The current board state
        preserve_word: If True, try to keep the word formed on the board for subsequent related words
    Returns:
        True if all blocks were moved successfully.
    """
    # Track all blocks and their positions for restoration
    original_positions = {}
    for block in board.blocks:
        original_positions[block] = block.position
    
    # First, identify all positions we need for the word
    word_positions = set()
    blocks_needed = {}  # Map target position -> block needed there
    
    # Track blocks that are already used in the current word formation
    used_blocks = set()
    
    # Find the current blocks that match the ones in the move
    updated_block_moves = []
    for original_block, target_pos in move.block_moves:
        # Get the letters of the original block
        letters = original_block.letters
        
        # Find a matching block on the current board that hasn't been used yet
        # Use the new letter-to-blocks index for faster lookup
        matching_blocks = []
        for letter in letters:
            letter_blocks = board.get_blocks_by_letter(letter)
            for block in letter_blocks:
                if block not in used_blocks and block.type == original_block.type:
                    # Check if all letters match
                    if all(l in block.letters for l in letters):
                        matching_blocks.append(block)
                        break
        
        # If no matching blocks found, try to find any block with the same letters
        if not matching_blocks:
            for block in board.blocks:
                if block not in used_blocks and block.type == original_block.type:
                    if all(l in block.letters for l in letters):
                        matching_blocks.append(block)
                        break
        
        if not matching_blocks:
            return False
        
        # Use the first matching block
        current_block = matching_blocks[0]
        
        # Mark this block as used
        used_blocks.add(current_block)
        
        # Add to updated moves
        updated_block_moves.append((current_block, target_pos))
        
        # Add to word positions and blocks needed
        row, col = target_pos
        word_positions.add((row, col))
        blocks_needed[target_pos] = current_block
        
        # Add second position for double blocks
        if current_block.type == BlockType.HORIZONTAL:
            word_positions.add((row, col + 1))
        elif current_block.type == BlockType.VERTICAL:
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
            # Try up to 2 times to move the block to a temporary position
            success = False
            for attempt in range(2):
                if move_word_bites_block(block, temp_pos[0], temp_pos[1], board):
                    temp_positions[block] = orig_pos
                    time.sleep(0.01)  # Further reduced delay after successful move
                    success = True
                    break
                time.sleep(0.01)  # Further reduced delay between attempts
            
            if not success:
                restore_blocks(original_positions, board)
                return False
        else:
            restore_blocks(original_positions, board)
            return False
    
    # Sort moves by position (top-to-bottom, left-to-right)
    sorted_moves = sorted(updated_block_moves, key=lambda x: (x[1][0], x[1][1]))
    
    # Move each block to its target position
    success = True
    for i, (block, target_pos) in enumerate(sorted_moves):
        # Skip if block is already in correct position
        if block.position == target_pos:
            continue
        
        # Try to move the block
        attempts = 0
        while attempts < 2:  # Reduced to 2 attempts
            if move_word_bites_block(block, target_pos[0], target_pos[1], board):
                time.sleep(0.005)  # Further reduced delay after successful move
                break
            attempts += 1
            time.sleep(0.005)  # Further reduced delay between attempts
        
        if attempts == 2:
            success = False
            break
    
    # If we failed, restore all blocks to their original positions
    if not success:
        restore_blocks(original_positions, board)
    elif not preserve_word:
        # Wait a bit to let the game register the word
        time.sleep(0.05)  # Further reduced delay
    
    return success

def restore_blocks(original_positions: dict, board: WordBitesBoard) -> None:
    """Helper function to restore blocks to their original positions"""
    # Sort blocks by position (bottom-to-top, right-to-left)
    blocks_to_restore = sorted(original_positions.items(), 
                             key=lambda x: (-x[1][0], -x[1][1]))
    
    # Create a map of block letters to current blocks on the board for faster lookup
    letter_to_blocks = {}
    for r in range(board.ROWS):
        for c in range(board.COLS):
            check_block = board.get_block_at(r, c)
            if check_block:
                letters_key = "".join(check_block.letters) + str(check_block.type)
                if letters_key not in letter_to_blocks:
                    letter_to_blocks[letters_key] = []
                letter_to_blocks[letters_key].append((check_block, (r, c)))
    
    # Track blocks that have already been moved to avoid redundant moves
    moved_blocks = set()
    
    for original_block, orig_pos in blocks_to_restore:
        # Skip if already in correct position
        letters_key = "".join(original_block.letters) + str(original_block.type)
        matching_blocks = letter_to_blocks.get(letters_key, [])
        
        # Find a block that's not already in the correct position and hasn't been moved yet
        current_block = None
        current_pos = None
        
        for block, pos in matching_blocks:
            if pos != orig_pos and block not in moved_blocks:  # Only consider blocks not already in position and not moved
                current_block = block
                current_pos = pos
                break
        
        if not current_block or current_pos == orig_pos:
            continue
            
        # Mark this block as moved
        moved_blocks.add(current_block)
            
        # Try to restore the block
        move_word_bites_block(current_block, orig_pos[0], orig_pos[1], board)
        time.sleep(0.005)  # Further reduced delay between moves

def execute_word_bites_moves(moves: List[WordBitesMove], board: WordBitesBoard) -> None:
    """
    Execute a list of Word Bites moves in order, prioritizing high-scoring words first.
    
    The moves are pre-sorted by optimize_word_order to prioritize:
    1. Words with the highest point values first
    2. Groups of related words with similar point values (within a 400-point threshold)
    3. Shorter words before longer words within each group
    
    Words that are related (like "think", "thinks", "thinker") with similar scores will be executed
    back-to-back with shorter delays between them, improving efficiency while still
    prioritizing the highest-scoring words overall.
    
    For related words (e.g., "ICEWORM" and "ICEWORMS"), the function will attempt to build
    upon the previous word rather than rebuilding the entire word from scratch, which
    significantly improves efficiency.
    
    The function ensures words don't have leading or trailing unrelated letters,
    so "UNTHINK" and "THINK" would not be considered related despite sharing
    a common stem.
    """
    from word_finder import are_words_related
    
    total_score = 0
    words_formed = 0
    failed_words = []
    
    # Keep track of the last successfully formed word and its block positions
    last_word = None
    last_word_blocks = {}  # Maps position -> block
    
    # Identify groups of related words
    i = 0
    while i < len(moves):
        # Start a new group with the current word
        current_word = moves[i].word
        related_words = [moves[i]]
        
        # Look ahead for related words
        j = i + 1
        while j < len(moves) and are_words_related(current_word, moves[j].word):
            related_words.append(moves[j])
            j += 1
        
        # Execute each word in the group
        for idx, move in enumerate(related_words):
            # For related words, try to preserve the word formation for the next word
            preserve_word = (idx < len(related_words) - 1)
            
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
                        modified_move = WordBitesMove(move.word, modified_block_moves, move.score)
                        success = execute_word_bites_move(modified_move, board, preserve_word)
                    else:
                        # If no new blocks needed (shouldn't happen), use the original move
                        success = execute_word_bites_move(move, board, preserve_word)
                
                elif last_word.startswith(move.word):
                    # The new word is a prefix of the last word (e.g., "PLAYER" -> "PLAY")
                    # This is less common but possible
                    success = True  # No need to do anything, the word is already formed
                
                else:
                    # The words are related but one is not a prefix of the other
                    # (e.g., "PLAY" -> "PLAYING" where we need to remove 'Y' and add 'YING')
                    success = execute_word_bites_move(move, board, preserve_word)
            else:
                # No previous word or words are not related, execute normally
                success = execute_word_bites_move(move, board, preserve_word)
            
            if success:
                total_score += move.score
                words_formed += 1
                
                # Update the last word and its block positions
                last_word = move.word
                last_word_blocks = {}
                for block, pos in move.block_moves:
                    # Find the actual block at this position
                    actual_block = board.get_block_at(pos[0], pos[1])
                    if actual_block:
                        last_word_blocks[pos] = actual_block
                
                # Use a shorter delay between related words
                if idx < len(related_words) - 1:  # If not the last word in the group
                    time.sleep(0.03)  # Further reduced delay between related words
                else:
                    time.sleep(0.05)  # Further reduced delay after completing a group
            else:
                failed_words.append(move)
                # If we fail to form a word, wait a bit before trying the next one
                time.sleep(0.03)  # Further reduced delay after failure
                # Reset last word tracking since we failed
                last_word = None
                last_word_blocks = {}
        
        # Move to the next group
        i = j
        # Reset last word tracking between unrelated groups
        last_word = None
        last_word_blocks = {}
    
    # Try the failed words one more time with a different approach
    if failed_words:
        for move in failed_words:
            # Try with a different approach - sort blocks differently
            # This time sort by distance from current position to target
            block_moves = []
            for block, target_pos in move.block_moves:
                current_pos = block.position
                distance = abs(current_pos[0] - target_pos[0]) + abs(current_pos[1] - target_pos[1])
                block_moves.append((block, target_pos, distance))
            
            # Sort by distance (closest first)
            block_moves.sort(key=lambda x: x[2])
            
            # Create a new move with reordered blocks
            from word_finder import WordBitesMove
            reordered_move = WordBitesMove(move.word, [(b, p) for b, p, _ in block_moves], move.score)
            
            if execute_word_bites_move(reordered_move, board, False):
                total_score += move.score
                words_formed += 1
            
            time.sleep(0.001)  # Further reduced delay after retry

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
            
            # Move to letter position with a small delay
            move = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, (x, y), 0)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, move)
            
            # Click down with delay
            down = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, (x, y), 0)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
            
            # Click up with delay
            up = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, (x, y), 0)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
            time.sleep(0.05)  # Longer delay between letters
        
        # Click enter button
        # Move to enter button with delay
        move = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, (enter_x, enter_y), 0)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, move)
        
        # Click down with delay
        down = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, (enter_x, enter_y), 0)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
        
        # Click up with delay
        up = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, (enter_x, enter_y), 0)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
        
        # Add longer delay after submitting word
        time.sleep(0.1)  # Longer delay after submitting each word
        
    except Exception as e:
        print(f"Error clicking anagram word: {str(e)}")