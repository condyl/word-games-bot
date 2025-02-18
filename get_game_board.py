import Quartz
import pyautogui
import time
from PIL import Image
import numpy as np
import cv2
import pytesseract

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

def find_game_board(image):
    opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    height, width = opencv_image.shape[:2]
    
    start_y = int(height * 0.47)
    end_y = int(height * 0.79)
    start_x = int(width * 0.11)
    end_x = int(width * 0.89)
    
    return opencv_image[start_y:end_y, start_x:end_x]

def process_cell(cell, row, col):
    """Process a single cell to extract its letter"""
    if cell is None or cell.size == 0:
        return '?'
    
    gray = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)
    
    # Try multiple approaches to get the best read
    methods = [
        # Standard threshold
        lambda: cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)[1],
        # Lower threshold for lighter letters
        lambda: cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)[1],
        # Higher threshold for darker letters
        lambda: cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)[1],
        # Adaptive threshold for varying brightness
        lambda: cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                    cv2.THRESH_BINARY_INV, 11, 2)
    ]
    
    for get_binary in methods:
        binary = get_binary()
        binary = cv2.resize(binary, (100, 100))
        
        # Add padding for better OCR
        padded = cv2.copyMakeBorder(binary, 20, 20, 20, 20, 
                                   cv2.BORDER_CONSTANT, value=0)
        
        # Try OCR with different configurations
        configs = [
            '--psm 10 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ',
            '--psm 6 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        ]
        
        for config in configs:
            text = pytesseract.image_to_string(padded, config=config).strip()
            if text and len(text) > 0:
                letter = text[0].upper()
                # If OCR thinks it's an A, check if it's actually a K
                if letter == 'A' and is_likely_K(binary):
                    return 'K'
                return letter
    
    return '?'

def is_likely_K(binary):
    """Check if a letter might be K based on its shape characteristics"""
    height, width = binary.shape
    
    # Look for strong vertical line on left
    left_col = binary[:, :width//3]
    left_pixels = np.sum(left_col == 255)
    has_vertical = left_pixels > (height * width/3 * 0.6)
    
    # Find the intersection point (where diagonals meet the vertical)
    mid_height = height // 2
    mid_width = width // 3
    
    # Check for intersection point
    intersection_region = binary[mid_height-5:mid_height+5, mid_width-5:mid_width+5]
    has_intersection = np.sum(intersection_region == 255) > 25
    
    # Check upper and lower diagonals
    upper_right = binary[:mid_height, mid_width:]
    lower_right = binary[mid_height:, mid_width:]
    
    upper_pixels = np.sum(upper_right == 255)
    lower_pixels = np.sum(lower_right == 255)
    
    # K should have roughly equal amounts of pixels in upper and lower diagonals
    diagonal_ratio = min(upper_pixels, lower_pixels) / max(upper_pixels, lower_pixels)
    has_balanced_diagonals = diagonal_ratio > 0.6
    
    # A key difference: K has less pixels in the middle horizontal region
    middle_horizontal = binary[mid_height-10:mid_height+10, mid_width:width]
    middle_density = np.sum(middle_horizontal == 255) / (middle_horizontal.size)
    has_middle_gap = middle_density < 0.3
    
    return (has_vertical and has_intersection and 
            has_balanced_diagonals and has_middle_gap)

def get_game_board():
    """Returns the current game board as a 2D list of letters"""
    window_bounds = find_iphone_window()
    if not window_bounds:
        return None
        
    # Capture screenshot
    padding = 20
    x = int(window_bounds['X']) + padding
    y = int(window_bounds['Y']) + padding
    width = int(window_bounds['Width']) - (2 * padding)
    height = int(window_bounds['Height']) - (2 * padding)
    screenshot = pyautogui.screenshot(region=(x, y, width, height))
    
    # Find and crop game board
    board_image = find_game_board(screenshot)
    if board_image is None:
        return None
        
    # Get dimensions and process cells
    height, width = board_image.shape[:2]
    cell_height = height // 4
    cell_width = width // 4
    
    # Process each cell
    grid = []
    for i in range(4):
        row = []
        for j in range(4):
            x = j * cell_width
            y = i * cell_height
            margin = 10
            cell = board_image[y+margin:y+cell_height-margin, x+margin:x+cell_width-margin]
            letter = process_cell(cell, i, j)
            row.append(letter)
        grid.append(row)
    
    return grid
