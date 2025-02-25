import Quartz
import pyautogui
import cv2
import numpy as np
import os
import time

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
                return window.get(Quartz.kCGWindowBounds)
                
    return None

def identify_game_version():
    # Create debug directory if it doesn't exist
    if not os.path.exists('debug'):
        os.makedirs('debug')
    
    window_bounds = find_iphone_window()
    if not window_bounds:
        return None
        
    # Capture screenshot using Quartz (macOS)
    padding = 20
    x = int(window_bounds['X']) + padding
    y = int(window_bounds['Y']) + padding
    width = int(window_bounds['Width']) - (2 * padding)
    height = int(window_bounds['Height']) - (2 * padding)
    
    # Get screen size
    screen = Quartz.CGDisplayBounds(Quartz.CGMainDisplayID())
    screen_height = int(screen.size.height)
    
    # Create CGImage
    region = Quartz.CGRectMake(x, y, width, height)
    image = Quartz.CGWindowListCreateImage(
        region,
        Quartz.kCGWindowListOptionOnScreenOnly,
        Quartz.kCGNullWindowID,
        Quartz.kCGWindowImageDefault
    )
    
    # Convert to PIL Image
    width = Quartz.CGImageGetWidth(image)
    height = Quartz.CGImageGetHeight(image)
    bytesperrow = Quartz.CGImageGetBytesPerRow(image)
    pixeldata = Quartz.CGDataProviderCopyData(Quartz.CGImageGetDataProvider(image))
    
    import PIL.Image
    screenshot = PIL.Image.frombytes('RGBA', (width, height), pixeldata, 'raw', 'BGRA')
    
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
    
    # Check which color has more pixels
    green_pixels = np.sum(green_mask > 0)
    purple_pixels = np.sum(purple_mask > 0)
    blue_pixels = np.sum(blue_mask > 0)
    
    # If blue is dominant and exceeds a threshold, it's Word Bites
    if blue_pixels > max(green_pixels, purple_pixels) and blue_pixels > (width * height * 0.3):
        return 'WORD_BITES'
    
    # Choose between green and purple for other games
    is_anagram = purple_pixels > green_pixels
    active_mask = purple_mask if is_anagram else green_mask
    
    # Crop and process mask
    height = active_mask.shape[0]
    if is_anagram:
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
        crop_start = int(height * 0.4)
        cropped_mask = active_mask[crop_start:, :]
    
    # Count cells
    inverted_mask = cv2.bitwise_not(cropped_mask)
    num_labels, _, _, _ = cv2.connectedComponentsWithStats(inverted_mask)
    num_cells = num_labels - 1  # Subtract background component
    
    # Identify the pattern
    if is_anagram:
        if 5 <= num_cells <= 6:  # More lenient detection for ANAGRAM6
            return 'ANAGRAM6'
        elif 6 <= num_cells <= 7:  # More lenient detection for ANAGRAM7
            return 'ANAGRAM7'
        else:
            return f'unknown_anagram ({num_cells} cells)'
    else:
        if num_cells == 16:
            return '4x4'
        elif num_cells == 20:
            return 'O'
        elif num_cells == 21:
            return 'X'
        elif num_cells == 25:
            return '5x5'
        else:
            return f'unknown_wordhunt ({num_cells} cells)'

def test_identification(image_path):
    """
    Test function to verify the identification works
    """
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not load image at {image_path}")
        return
    
    version = identify_game_version()
    print(f"Detected game version: {version}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_identification(sys.argv[1])
    else:
        print("Please provide an image path as argument") 