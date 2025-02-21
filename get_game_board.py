import Quartz
import pyautogui
import time
from PIL import Image
import numpy as np
import cv2
import pytesseract
import os
import argparse

# Cache OCR configs
OCR_CONFIGS = [
    '--psm 10 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ',
    '--psm 6 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ'
]

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
    
    # Define cropping dimensions based on game version
    if game_version == "4x4":
        # Original 4x4 dimensions
        start_y = int(height * 0.47)
        end_y = int(height * 0.79)
        start_x = int(width * 0.11)
        end_x = int(width * 0.89)
    elif game_version in ["X", "O", "5x5"]:
        # Larger dimensions for 5x5 grid variants
        start_y = int(height * 0.45)
        end_y = int(height * 0.81)  
        start_x = int(width * 0.06)
        end_x = int(width * 0.94)
    elif game_version.startswith("ANAGRAM"):
        # Specific dimensions for anagram modes
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
    else:
        raise ValueError(f"Unsupported game version: {game_version}")
    
    cropped = opencv_image[start_y:end_y, start_x:end_x]
    
    # Save cropped image with timestamp
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    cv2.imwrite(f'debug/board_{timestamp}.png', cropped)
    
    return cropped

def is_likely_P(binary):
    """Check if a letter might be P based on its shape characteristics"""
    height, width = binary.shape
    
    # Split the image into more detailed regions
    h_third = height // 3
    w_third = width // 3
    
    # Get regions for analysis
    left_col = binary[:, :w_third]
    top_right = binary[0:h_third, 2*w_third:]
    middle_right = binary[h_third:2*h_third, 2*w_third:]
    bottom_right = binary[2*h_third:, 2*w_third:]
    top_half = binary[:height//2, :]
    bottom_half = binary[height//2:, :]
    
    # Calculate densities
    left_density = np.sum(left_col == 255) / left_col.size
    top_density = np.sum(top_right == 255) / top_right.size
    middle_density = np.sum(middle_right == 255) / middle_right.size
    bottom_density = np.sum(bottom_right == 255) / bottom_right.size
    top_half_density = np.sum(top_half == 255) / top_half.size
    bottom_half_density = np.sum(bottom_half == 255) / bottom_half.size
    
    # Key characteristics of P:
    # 1. Strong vertical line on the left
    has_left_line = left_density > 0.5
    
    # 2. Curved part at top right
    has_top_curve = top_density > 0.3
    
    # 3. Very empty bottom right
    has_empty_bottom = bottom_density < 0.15
    
    # 4. Gap in middle right (where curve ends)
    has_middle_gap = middle_density < 0.25
    
    # 5. Top half should be significantly denser than bottom half
    top_bottom_ratio = top_half_density / bottom_half_density if bottom_half_density > 0 else float('inf')
    has_density_difference = top_bottom_ratio > 1.3
    
    # 6. Bottom right should be much emptier than top right
    top_bottom_right_ratio = top_density / bottom_density if bottom_density > 0 else float('inf')
    has_right_side_difference = top_bottom_right_ratio > 2.5
    
    # Combine all characteristics
    is_p = (has_left_line and 
            has_top_curve and 
            has_empty_bottom and 
            has_middle_gap and 
            has_density_difference and 
            has_right_side_difference)
    
    return is_p

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
        if cells_folder and idx == 0:
            cv2.imwrite(f'{cells_folder}/cell_{row}_{col}_processed.png', padded)
        
        # Try OCR with different configurations
        for config in OCR_CONFIGS:
            text = pytesseract.image_to_string(padded, config=config).strip()
            if text and len(text) > 0:
                letter = text[0].upper()
                # Always check for P if the letter could be confused with it
                if letter in ['D', 'B', 'P', 'R', 'E', 'F'] and is_likely_P(binary):
                    return 'P'
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

def move_mouse_away(window_bounds):
    """Move mouse just above the game board"""
    # Get window position
    window_x = window_bounds['X']
    window_y = window_bounds['Y']
    window_height = window_bounds['Height']
    window_width = window_bounds['Width']
    
    # Calculate position just above the game board
    # Using same ratios as board detection but slightly higher
    target_y = window_y + (window_height * 0.35)  # Above the 0.45 start_y of board
    target_x = window_x + (window_width * 0.5)    # Center horizontally
    
    # Move mouse to target position
    move = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, (target_x, target_y), 0)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, move)

def get_game_board(game_version="4x4"):
    """Returns the current game board as a 2D list of letters"""
    window_bounds = find_iphone_window()
    if not window_bounds:
        return None
        
    # Move mouse away before taking screenshot
    move_mouse_away(window_bounds)
    time.sleep(0.1)  # Small delay to ensure mouse has moved
    
    # Set padding based on game version
    padding = 0 if game_version.startswith("ANAGRAM") else 20
    
    # For anagram modes, adjust the capture region to maintain aspect ratio
    if game_version.startswith("ANAGRAM"):
        # Calculate aspect ratio of iPhone screen (typically 9:19.5)
        aspect_ratio = 9/19.5
        
        # Get window dimensions
        window_width = int(window_bounds['Width'])
        window_height = int(window_bounds['Height'])
        
        # Adjust capture region to maintain aspect ratio
        target_height = window_height
        target_width = int(target_height * aspect_ratio)
        
        # Center the capture region
        x_offset = (window_width - target_width) // 2
        x = int(window_bounds['X']) + x_offset
        y = int(window_bounds['Y'])
        width = target_width
        height = target_height
    else:
        # Normal padding-based capture for non-anagram modes
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
    
    # If it's an anagram mode, crop out the padding after capturing
    if game_version.startswith("ANAGRAM"):
        # Remove padding from all sides
        crop_box = (
            padding,  # left
            padding,  # top
            width - padding,  # right
            height - padding  # bottom
        )
        screenshot = screenshot.crop(crop_box)
    
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
    
    # Handle anagram modes differently
    if game_version.startswith("ANAGRAM"):
        # For anagrams, we'll process as a single row
        num_letters = 6 if game_version == "ANAGRAM6" else 7
        cell_width = width // num_letters
        
        # Add padding for better letter separation
        if game_version == "ANAGRAM7":
            h_padding = int(cell_width * 0.20)
            v_padding = 2
        else:  # ANAGRAM6
            h_padding = int(cell_width * 0.15)
            v_padding = 0
        
        # Create a single row for anagram letters
        row = []
        for j in range(num_letters):
            x = j * cell_width
            # Apply padding to each cell
            cell = board_image[v_padding:height-v_padding, x+h_padding:x+cell_width-h_padding]
            
            # Save the cell with margins
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            cells_folder = f'debug/cells_{timestamp}'
            if not os.path.exists(cells_folder):
                os.makedirs(cells_folder)
            cv2.imwrite(f'{cells_folder}/cell_0_{j}_margins.png', cell)
            
            # Process the cell
            letter = process_cell(cell, 0, j, cells_folder)
            row.append(letter)
        
        return [row]  # Return as a single-row grid for consistency
    
    # Original grid processing for non-anagram modes
    else:
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
        
        # Determine grid size based on game version
        if game_version == "4x4":
            grid_size = 4
        elif game_version in ["X", "O", "5x5"]:
            grid_size = 5
        else:
            raise ValueError(f"Unsupported game version: {game_version}")
            
        cell_height = height // grid_size
        cell_width = width // grid_size
        print(f"Grid size: {grid_size}x{grid_size}")
        print(f"Cell dimensions: {cell_width}x{cell_height}")
        
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

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Debug game board detection')
    parser.add_argument('--version', type=str, default="4x4",
                      help='Game version (4x4, 5x5, X, O, ANAGRAM6, ANAGRAM7)')
    parser.add_argument('--continuous', action='store_true',
                      help='Continuously capture boards until interrupted')
    
    args = parser.parse_args()
    
    def run_detection():
        print(f"\nDetecting game board for version: {args.version}")
        board = get_game_board(args.version)
        
        if board is None:
            print("Failed to detect game board - is the iPhone window visible?")
            return
        
        print("\nDetected board:")
        for row in board:
            print(' '.join(row))
        print("\nCheck the debug folder for captured images")
    
    try:
        if args.continuous:
            print("Press Ctrl+C to stop continuous detection")
            while True:
                run_detection()
                time.sleep(2)  # Wait 2 seconds between captures
        else:
            run_detection()
    except KeyboardInterrupt:
        print("\nDetection stopped by user")
    except Exception as e:
        print(f"\nError occurred: {e}")
