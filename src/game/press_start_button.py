import Quartz
import time
from src.utils.window import find_iphone_window

def focus_and_click_start():
    """Focus on the iPhone window and click the start button."""
    window = find_iphone_window()
    if not window:
        print("Could not find iPhone window")
        return False
        
    # Calculate position for both game types
    target_x_word_hunt = window['x'] + (window['width'] / 2)
    target_y_word_hunt = window['y'] + (window['height'] * 0.71)
    target_x_anagrams = window['x'] + (window['width'] / 2)
    target_y_anagrams = window['y'] + (window['height'] * 0.66)

    # First click might focus the window, second click starts the game
    for i in range(2):
        move = Quartz.CGEventCreateMouseEvent(
            None,
            Quartz.kCGEventMouseMoved,
            (target_x_word_hunt, target_y_word_hunt),
            0
        )
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, move)
        time.sleep(0.2)  # Increased delay to ensure window focus
        
        # Click down
        down = Quartz.CGEventCreateMouseEvent(
            None,
            Quartz.kCGEventLeftMouseDown,
            (target_x_word_hunt, target_y_word_hunt),
            0
        )
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
        time.sleep(0.1)
        
        # Click up
        up = Quartz.CGEventCreateMouseEvent(
            None,
            Quartz.kCGEventLeftMouseUp,
            (target_x_word_hunt, target_y_word_hunt),
            0
        )
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)

    # Anagrams
    move = Quartz.CGEventCreateMouseEvent(
        None,
        Quartz.kCGEventMouseMoved,
        (target_x_anagrams, target_y_anagrams),
        0
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, move)
    # Click down
    down = Quartz.CGEventCreateMouseEvent(
        None,
        Quartz.kCGEventLeftMouseDown,
        (target_x_anagrams, target_y_anagrams),
        0
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
    time.sleep(0.1)
    
    # Click up
    up = Quartz.CGEventCreateMouseEvent(
        None,
        Quartz.kCGEventLeftMouseUp,
        (target_x_anagrams, target_y_anagrams),
        0
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
        
    return True

if __name__ == "__main__":
    # Test the function
    print("Testing start button position...")
    focus_and_click_start() 