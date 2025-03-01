import Quartz
import time
import pyautogui  # Add pyautogui for more robust mouse control

def get_iphone_window():
    """Get the iPhone mirroring window position and dimensions."""
    # List of possible window title keywords for iPhone mirroring
    iphone_keywords = ['iPhone', 'iOS', 'QuickTime Player']
    
    windows = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
        Quartz.kCGNullWindowID
    )
    
    for window in windows:
        name = window.get(Quartz.kCGWindowName, '')
        owner = window.get(Quartz.kCGWindowOwnerName, '')
        
        # Check for iPhone-related keywords in both window name and owner
        for keyword in iphone_keywords:
            if (keyword.lower() in name.lower() or 
                keyword.lower() in owner.lower()):
                bounds = window.get(Quartz.kCGWindowBounds)
                print(f"Found iPhone window: '{name}' by '{owner}'")
                return {
                    'x': bounds['X'],
                    'y': bounds['Y'],
                    'width': bounds['Width'],
                    'height': bounds['Height']
                }
    
    print("No iPhone window found. Available windows:")
    for window in windows:
        name = window.get(Quartz.kCGWindowName, '')
        owner = window.get(Quartz.kCGWindowOwnerName, '')
        if name or owner:
            print(f"- '{name}' by '{owner}'")
    
    return None

def click_at_position(x, y, clicks=1, interval=0.1):
    """Click at the specified position using pyautogui for more reliability."""
    try:
        # Move to position
        pyautogui.moveTo(x, y, duration=0.2)
        time.sleep(0.1)  # Short pause after movement
        
        # Click
        pyautogui.click(x=x, y=y, clicks=clicks, interval=interval)
        return True
    except Exception as e:
        print(f"Error clicking at position ({x}, {y}): {str(e)}")
        return False

def focus_and_click_start():
    """Focus the iPhone window and click the start button."""
    window = get_iphone_window()
    if not window:
        print("iPhone window not found")
        return False
    
    print(f"iPhone window found at: x={window['x']}, y={window['y']}, width={window['width']}, height={window['height']}")
        
    # Calculate positions for different game types
    # Word Hunt / Word Bites position
    target_x_word_hunt = window['x'] + (window['width'] / 2)
    target_y_word_hunt = window['y'] + (window['height'] * 0.71)
    
    # Anagrams position
    target_x_anagrams = window['x'] + (window['width'] / 2)
    target_y_anagrams = window['y'] + (window['height'] * 0.66)
    
    # Word Bites specific position (slightly higher)
    target_x_word_bites = window['x'] + (window['width'] / 2)
    target_y_word_bites = window['y'] + (window['height'] * 0.68)

    # First click to focus the window
    print("Clicking to focus window...")
    window_center_x = window['x'] + (window['width'] / 2)
    window_center_y = window['y'] + (window['height'] / 2)
    click_at_position(window_center_x, window_center_y)
    time.sleep(0.5)  # Wait for window to focus
    
    # Try clicking at Word Hunt position
    print(f"Clicking Word Hunt start button at ({target_x_word_hunt}, {target_y_word_hunt})...")
    click_at_position(target_x_word_hunt, target_y_word_hunt)
    time.sleep(0.5)
    
    # Try clicking at Anagrams position
    print(f"Clicking Anagrams start button at ({target_x_anagrams}, {target_y_anagrams})...")
    click_at_position(target_x_anagrams, target_y_anagrams)
    time.sleep(0.5)
    
    # Try clicking at Word Bites position
    print(f"Clicking Word Bites start button at ({target_x_word_bites}, {target_y_word_bites})...")
    click_at_position(target_x_word_bites, target_y_word_bites)
    
    # Wait a moment to let the game start
    time.sleep(0.5)
    
    return True

if __name__ == "__main__":
    # Test the function
    print("Testing start button position...")
    focus_and_click_start() 