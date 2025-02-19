import Quartz
import pyautogui
import time
from PIL import Image
import numpy as np
import cv2
import pytesseract
import os

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

def find_game_board(image, game_version):
    # Create debug directory if it doesn't exist
    if not os.path.exists('debug'):
        os.makedirs('debug')
        
    opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    height, width = opencv_image.shape[:2]
    
    if game_version == "4x4":
        # Original 4x4 dimensions
        start_y = int(height * 0.47)
        end_y = int(height * 0.79)
        start_x = int(width * 0.11)
        end_x = int(width * 0.89)
    else:  # Handles "X", "O", and "5x5" versions
        # Larger dimensions for 5x5 grid variants
        start_y = int(height * 0.44)
        end_y = int(height * 0.82)  
        start_x = int(width * 0.06)
        end_x = int(width * 0.94)     
    
    cropped = opencv_image[start_y:end_y, start_x:end_x]
    
    # Save cropped image with timestamp
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    cv2.imwrite(f'debug/board_{timestamp}.png', cropped)
    
    return cropped

def process_cell(cell, row, col, cells_folder=None):
    """Process a single cell to extract its letter"""
    if cell is None or cell.size == 0:
        print(f"Warning: Empty cell at ({row},{col})")
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
    
    for idx, get_binary in enumerate(methods):
        binary = get_binary()
        binary = cv2.resize(binary, (100, 100))
        
        # Add padding for better OCR
        padded = cv2.copyMakeBorder(binary, 20, 20, 20, 20, 
                                   cv2.BORDER_CONSTANT, value=0)
        
        # Save the processed cell image if a folder is provided
        if cells_folder and idx == 0:  # Save only the first method's result
            cv2.imwrite(f'{cells_folder}/cell_{row}_{col}_processed.png', padded)
        
        # Try OCR with different configurations
        configs = [
            '--psm 10 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ',
            '--psm 6 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        ]
        
        for config in configs:
            text = pytesseract.image_to_string(padded, config=config).strip()
            if text and len(text) > 0:
                letter = text[0].upper()
                if letter == 'A' and is_likely_K(binary):
                    return 'K'
                return letter
    
    print(f"Warning: Failed to detect letter at ({row},{col})")
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

def get_game_board(game_version="4x4"):
    """Returns the current game board as a 2D list of letters"""
    window_bounds = find_iphone_window()
    if not window_bounds:
        return None
        
    # Capture screenshot using Quartz (macOS)
    padding = 20
    x = int(window_bounds['X']) + padding
    y = int(window_bounds['Y']) + padding
    width = int(window_bounds['Width']) - (2 * padding)
    height = int(window_bounds['Height']) - (2 * padding)
    
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
    
    # Find and crop game board
    board_image = find_game_board(screenshot, game_version)
    if board_image is None:
        return None
        
    # Create debug directory if it doesn't exist
    if not os.path.exists('debug'):
        os.makedirs('debug')
    
    # Get dimensions and process cells
    height, width = board_image.shape[:2]
    print(f"\nProcessing {game_version} board ({width}x{height})")
    
    # Determine grid size based on game version
    grid_size = 4 if game_version == "4x4" else 5
    cell_height = height // grid_size
    cell_width = width // grid_size
    print(f"Grid size: {grid_size}x{grid_size}")
    print(f"Cell dimensions: {cell_width}x{cell_height}")
    
    # Define empty cells for X and O versions
    empty_cells = set()
    if game_version == "X":
        empty_cells = {(2,0), (0,2), (4,2), (2,4)}
    elif game_version == "O":
        empty_cells = {(0,0), (0,4), (2,2), (4,0), (4,4)}
    
    # Create timestamped folder for this board's cells
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    cells_folder = f'debug/cells_{timestamp}'
    if not os.path.exists(cells_folder):
        os.makedirs(cells_folder)
    
    # Process each cell
    grid = []
    for i in range(grid_size):
        row = []
        for j in range(grid_size):
            if (i,j) in empty_cells:
                row.append(' ')  # or whatever character you want to use for empty cells
                continue
                
            x = j * cell_width
            y = i * cell_height
            # Increase margins to 20 pixels
            margin = 16
            cell = board_image[y+margin:y+cell_height-margin, x+margin:x+cell_width-margin]
            
            # Save the cell with margins
            cv2.imwrite(f'{cells_folder}/cell_{i}_{j}_margins.png', cell)
            
            # Process the cell
            letter = process_cell(cell, i, j, cells_folder)
            row.append(letter)
        grid.append(row)
    
    # Print final grid
    print("\nFinal grid:")
    for row in grid:
        print(' '.join(row))
    
    return grid
