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

def get_letter_position(x: int, y: int, board_size: int = 4) -> Tuple[int, int]:
    """
    Convert board coordinates (0-3, 0-3) to screen coordinates.
    Note: Input coordinates are (row, col) format
    """
    window = get_iphone_window()
    if not window:
        raise Exception("iPhone window not found")
    
    # Match the exact region calculation from get_game_board.py
    width = window['width']
    height = window['height']
    
    # Use the exact same margins as get_game_board.py
    start_y = int(height * 0.47)
    end_y = int(height * 0.79)
    start_x = int(width * 0.11)
    end_x = int(width * 0.89)
    
    # Calculate board dimensions
    board_width = end_x - start_x
    board_height = end_y - start_y
    
    # Calculate cell size
    cell_width = board_width / board_size
    cell_height = board_height / board_size
    
    # Swap x and y to match the grid orientation
    # y coordinate determines horizontal position (column)
    # x coordinate determines vertical position (row)
    screen_x = window['x'] + start_x + (cell_width * y) + (cell_width / 2)
    screen_y = window['y'] + start_y + (cell_height * x) + (cell_height / 2)
    
    return (int(screen_x), int(screen_y))

def draw_word(path: List[Tuple[int, int]]):
    """
    Draw a word by dragging the mouse through the given path using Quartz events.
    """
    if not path:
        return
    
    # Get start position
    start_x, start_y = get_letter_position(path[0][0], path[0][1])
    
    try:
        # Move to start position
        move = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, (start_x, start_y), 0)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, move)
        
        # Press mouse down
        down = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, (start_x, start_y), 0)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
        
        # Drag through all points
        for i, (x, y) in enumerate(path[1:], 1):
            screen_x, screen_y = get_letter_position(x, y)
            drag = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDragged, (screen_x, screen_y), 0)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, drag)
            time.sleep(0.06)
            
    finally:
        # Release at end
        up = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, (screen_x, screen_y), 0)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
        time.sleep(0.05)

def draw_all_words(words: dict[str, List[Tuple[int, int]]], min_length: int = 3):
    """
    Draw all words in the found_words dictionary.
    Draws longer words first (they're worth more points).
    """
    # Sort words by length (longest first) and alphabetically
    sorted_words = sorted(words.items(), key=lambda x: (-len(x[0]), x[0]))
    
    for word, path in sorted_words:
        if len(word) >= min_length:
            print(f"Drawing: {word}")
            draw_word(path)