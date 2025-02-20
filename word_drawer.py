import time
from typing import List, Tuple
import Quartz

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