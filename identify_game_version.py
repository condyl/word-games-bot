import Quartz
import pyautogui
import cv2
import numpy as np
import os
import time
import PIL.Image
import traceback

def find_iphone_window():
    # List of possible window title keywords for iPhone mirroring
    iphone_keywords = ['iPhone', 'iOS', 'QuickTime Player']
    
    # Get all windows
    windows = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
        Quartz.kCGNullWindowID
    )
    
    # Check if this is an iPhone window
    for window in windows:
        title = window.get(Quartz.kCGWindowName, 'Unknown')
        owner = window.get(Quartz.kCGWindowOwnerName, 'Unknown')
        
        for keyword in iphone_keywords:
            if (keyword.lower() in str(title).lower() or 
                keyword.lower() in str(owner).lower()):
                print(f"Found iPhone window: '{title}' by '{owner}'")
                return window.get(Quartz.kCGWindowBounds)
    
    print("No iPhone window found. Available windows:")
    for window in windows:
        title = window.get(Quartz.kCGWindowName, 'Unknown')
        owner = window.get(Quartz.kCGWindowOwnerName, 'Unknown')
        if title != 'Unknown' or owner != 'Unknown':
            print(f"- '{title}' by '{owner}'")
                
    return None

def identify_game_version():
    try:
        # Create debug directory if it doesn't exist
        if not os.path.exists('debug'):
            os.makedirs('debug')
        
        print("Looking for iPhone window...")
        window_bounds = find_iphone_window()
        if not window_bounds:
            print("No iPhone window found")
            return None
        
        print(f"iPhone window found at: x={window_bounds['X']}, y={window_bounds['Y']}, width={window_bounds['Width']}, height={window_bounds['Height']}")
            
        # Capture screenshot using Quartz (macOS)
        padding = 20
        x = int(window_bounds['X']) + padding
        y = int(window_bounds['Y']) + padding
        width = int(window_bounds['Width']) - (2 * padding)
        height = int(window_bounds['Height']) - (2 * padding)
        
        # Get screen size
        screen = Quartz.CGDisplayBounds(Quartz.CGMainDisplayID())
        screen_height = int(screen.size.height)
        
        print(f"Capturing screenshot at: x={x}, y={y}, width={width}, height={height}")
        
        # Create CGImage
        region = Quartz.CGRectMake(x, y, width, height)
        image = Quartz.CGWindowListCreateImage(
            region,
            Quartz.kCGWindowListOptionOnScreenOnly,
            Quartz.kCGNullWindowID,
            Quartz.kCGWindowImageDefault
        )
        
        if image is None:
            print("Failed to capture screenshot")
            return None
        
        # Convert to PIL Image
        width = Quartz.CGImageGetWidth(image)
        height = Quartz.CGImageGetHeight(image)
        bytesperrow = Quartz.CGImageGetBytesPerRow(image)
        pixeldata = Quartz.CGDataProviderCopyData(Quartz.CGImageGetDataProvider(image))
        
        screenshot = PIL.Image.frombytes('RGBA', (width, height), pixeldata, 'raw', 'BGRA')
        
        # Save debug image
        debug_path = os.path.join('debug', 'game_screenshot.png')
        screenshot.save(debug_path)
        print(f"Saved debug screenshot to {debug_path}")
        
        # Convert to OpenCV format and HSV
        opencv_image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        hsv = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2HSV)
        
        # Create masks for green, purple, and blue (Word Bites)
        lower_green = np.array([40, 40, 40])
        upper_green = np.array([80, 255, 255])
        lower_purple = np.array([120, 20, 40])
        upper_purple = np.array([150, 100, 255])
        lower_blue = np.array([100, 50, 50])
        upper_blue = np.array([120, 255, 255])
        
        green_mask = cv2.inRange(hsv, lower_green, upper_green)
        purple_mask = cv2.inRange(hsv, lower_purple, upper_purple)
        blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
        
        # Save debug masks
        cv2.imwrite(os.path.join('debug', 'green_mask.png'), green_mask)
        cv2.imwrite(os.path.join('debug', 'purple_mask.png'), purple_mask)
        cv2.imwrite(os.path.join('debug', 'blue_mask.png'), blue_mask)
        
        # Check which color has more pixels
        green_pixels = np.sum(green_mask > 0)
        purple_pixels = np.sum(purple_mask > 0)
        blue_pixels = np.sum(blue_mask > 0)
        
        print(f"Color detection: Green pixels: {green_pixels}, Purple pixels: {purple_pixels}, Blue pixels: {blue_pixels}")
        
        # If blue is dominant and exceeds a threshold, it's Word Bites
        if blue_pixels > max(green_pixels, purple_pixels) and blue_pixels > (width * height * 0.3):
            print("Detected Word Bites based on blue color dominance")
            return 'WORD_BITES'
        
        # Choose between green and purple for other games
        is_anagram = purple_pixels > green_pixels
        active_mask = purple_mask if is_anagram else green_mask
        
        # Crop and process mask
        height = active_mask.shape[0]
        if is_anagram:
            print("Processing as potential Anagram game")
            # Adjust crop region for anagrams
            crop_start = int(height * 0.75)  # Move crop region lower
            crop_end = int(height * 0.85)    # Reduce crop height
            cropped_mask = active_mask[crop_start:crop_end, :]
            
            # More aggressive thresholding for anagrams
            _, cropped_mask = cv2.threshold(cropped_mask, 100, 255, cv2.THRESH_BINARY)
            
            # Use smaller kernel for anagram morphology
            kernel = np.ones((3,3), np.uint8)
            cropped_mask = cv2.morphologyEx(cropped_mask, cv2.MORPH_CLOSE, kernel)
            cropped_mask = cv2.morphologyEx(cropped_mask, cv2.MORPH_OPEN, kernel)
        else:
            print("Processing as potential Word Hunt game")
            crop_start = int(height * 0.4)
            cropped_mask = active_mask[crop_start:, :]
        
        # Save cropped mask for debugging
        cv2.imwrite(os.path.join('debug', 'cropped_mask.png'), cropped_mask)
        
        # Count cells
        inverted_mask = cv2.bitwise_not(cropped_mask)
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(inverted_mask)
        num_cells = num_labels - 1  # Subtract background component
        
        print(f"Detected {num_cells} cells in the game board")
        
        # Identify the pattern
        if is_anagram:
            if 5 <= num_cells <= 6:  # More lenient detection for ANAGRAM6
                print("Identified as ANAGRAM6")
                return 'ANAGRAM6'
            elif 6 <= num_cells <= 7:  # More lenient detection for ANAGRAM7
                print("Identified as ANAGRAM7")
                return 'ANAGRAM7'
            else:
                print(f"Unknown anagram type with {num_cells} cells")
                return f'unknown_anagram ({num_cells} cells)'
        else:
            if num_cells == 16:
                print("Identified as 4x4 Word Hunt")
                return '4x4'
            elif num_cells == 20:
                print("Identified as O-shaped Word Hunt")
                return 'O'
            elif num_cells == 21:
                print("Identified as X-shaped Word Hunt")
                return 'X'
            elif num_cells == 25:
                print("Identified as 5x5 Word Hunt")
                return '5x5'
            else:
                print(f"Unknown Word Hunt type with {num_cells} cells")
                return f'unknown_wordhunt ({num_cells} cells)'
    except Exception as e:
        print(f"Error in identify_game_version: {str(e)}")
        print(traceback.format_exc())
        return f"unknown (Error: {str(e)})"

def test_identification(image_path=None):
    """
    Test function to verify the identification works
    """
    if image_path:
        # Test with provided image
        image = cv2.imread(image_path)
        if image is None:
            print(f"Error: Could not load image at {image_path}")
            return
    
    # Test live identification
    version = identify_game_version()
    print(f"Detected game version: {version}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_identification(sys.argv[1])
    else:
        test_identification() 