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
    
    # Convert to OpenCV format
    opencv_image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    
    # Convert to HSV
    hsv = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2HSV)
    
    # Create green mask
    lower_green = np.array([40, 40, 40])
    upper_green = np.array([80, 255, 255])
    green_mask = cv2.inRange(hsv, lower_green, upper_green)
    
    # Crop green mask to bottom 60%
    height = green_mask.shape[0]
    crop_start = int(height * 0.4)  # Start at 40% from top
    green_mask = green_mask[crop_start:, :]  # Crop from 40% to bottom
    
    # Count black regions (cells)
    inverted_mask = cv2.bitwise_not(green_mask)
    num_labels, _, _, _ = cv2.connectedComponentsWithStats(inverted_mask)
    num_cells = num_labels - 1  # Subtract 1 because it includes the background
    
    # Identify the pattern based on number of cells
    if num_cells == 16:
        return '4x4'
    elif num_cells == 20:
        return 'O'
    elif num_cells == 21:
        return 'X'
    elif num_cells == 25:
        return '5x5'
    else:
        return f'unknown ({num_cells} cells)'

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