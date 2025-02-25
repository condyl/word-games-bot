import Quartz
import pyautogui
import time
from PIL import Image
import numpy as np
import cv2
import easyocr
import os
import argparse
from word_bites_board import WordBitesBoard, Block, BlockType

# Initialize EasyOCR reader globally (it's slow to initialize)
READER = easyocr.Reader(['en'], gpu=False)

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
    elif game_version == "WORD_BITES":
        # Word Bites dimensions - ADJUST THESE VALUES AS NEEDED
        start_y = int(height * 0.36) 
        end_y = int(height * 0.85) 
        start_x = int(width * 0) 
        end_x = int(width * 1) 
    else:
        raise ValueError(f"Unsupported game version: {game_version}")
    
    cropped = opencv_image[start_y:end_y, start_x:end_x]
    
    # Add horizontal padding for Word Bites
    if game_version == "WORD_BITES":
        padding = 10  # Adjust this value as needed
        # Create new image with padding
        padded = cv2.copyMakeBorder(
            cropped,
            top=0,
            bottom=0,
            left=padding,
            right=padding,
            borderType=cv2.BORDER_CONSTANT,
            value=[255, 255, 255]  # White padding
        )
        cropped = padded
    
    # Save cropped image with timestamp
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    cv2.imwrite(f'debug/board_{timestamp}.png', cropped)
    
    return cropped

def process_cell(cell, row, col, cells_folder=None):
    """Process a single cell to extract its letter"""
    if cell is None or cell.size == 0:
        print(f"Warning: Empty cell at ({row},{col})")
        return '?'
        
    # Convert to grayscale
    gray = cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)
    
    # Resize to a larger size for better OCR
    gray = cv2.resize(gray, (200, 200))
    
    # Apply adaptive histogram equalization
    clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(4,4))
    gray = clahe.apply(gray)
    
    # Try multiple preprocessing approaches
    methods = [
        # Standard Otsu's thresholding
        lambda: cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1],
        
        # Fixed threshold for consistency
        lambda: cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)[1],
        
        # Adaptive thresholding
        lambda: cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                    cv2.THRESH_BINARY_INV, 15, 5),
    ]
    
    best_result = None
    max_confidence = 0
    
    for idx, get_binary in enumerate(methods):
        binary = get_binary()
        
        # Standard morphological operations
        kernel = np.ones((2,2), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        # Add padding
        binary = cv2.copyMakeBorder(binary, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=0)
        
        # Save debug images if requested
        if cells_folder and idx == 0:
            cv2.imwrite(f'{cells_folder}/cell_{row}_{col}_binary.png', binary)
        
        try:
            # Use EasyOCR with confidence scores
            result = READER.readtext(binary, 
                                   allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                                   batch_size=1,
                                   detail=1)
            
            if result and len(result) > 0:
                text = result[0][1].upper()
                confidence = result[0][2]
                
                # Ensure we only take the first character
                if len(text) > 1:
                    print(f"Warning: OCR returned multiple characters '{text}' at ({row},{col}), using only first character")
                    text = text[0]
                
                # Keep track of the highest confidence result
                if confidence > max_confidence:
                    max_confidence = confidence
                    best_result = text
                
                # If we get a high confidence result, return immediately
                if confidence > 0.8:
                    return text
                
        except Exception as e:
            print(f"Warning: OCR failed for cell ({row},{col}): {str(e)}")
            continue
    
    # Return the highest confidence result if we found one
    if best_result:
        # Ensure we only return a single character
        if len(best_result) > 1:
            print(f"Warning: Best OCR result has multiple characters '{best_result}' at ({row},{col}), using only first character")
            best_result = best_result[0]
        return best_result
    
    print(f"Warning: Failed to detect letter at ({row},{col}), assuming it's an I")
    return 'I'  # Default to I instead of '?' when recognition fails

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

def is_mostly_blue(cell_image):
    """Check if a cell is mostly blue (background)"""
    # Convert to HSV for better color detection
    hsv = cv2.cvtColor(cell_image, cv2.COLOR_BGR2HSV)
    
    # Define blue range in HSV
    lower_blue = np.array([100, 50, 50])
    upper_blue = np.array([130, 255, 255])
    
    # Create mask for blue pixels
    blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
    
    # Calculate percentage of blue pixels
    total_pixels = cell_image.shape[0] * cell_image.shape[1]
    blue_pixels = np.count_nonzero(blue_mask)
    blue_percentage = blue_pixels / total_pixels
    
    return blue_percentage > 0.5  # Return True if more than 50% is blue

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
    
    # Handle Word Bites differently
    if game_version == "WORD_BITES":
        # Create a Word Bites board
        board = WordBitesBoard()
        
        # Use full width and height including padding
        cell_height = height // board.ROWS
        cell_width = width // board.COLS
        
        # Create timestamped folder for this board's cells
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        cells_folder = f'debug/cells_{timestamp}'
        if not os.path.exists(cells_folder):
            os.makedirs(cells_folder)
        
        # Create a copy of the image for grid lines
        debug_image = board_image.copy()
        
        # Draw horizontal lines (10 lines for 9 rows)
        for i in range(board.ROWS + 1):  # 10 lines = 9 rows
            y = int(i * (height / board.ROWS))
            cv2.line(debug_image, (0, y), (width, y), (0, 255, 0), 1)
        
        # Draw vertical lines (9 lines for 8 columns)
        for j in range(board.COLS + 1):  # 9 lines = 8 columns
            x = int(j * (width / board.COLS))
            cv2.line(debug_image, (x, 0), (x, height), (0, 255, 0), 1)
            
        cv2.imwrite(f'{cells_folder}/grid_lines.png', debug_image)
        
        # Process each cell
        for i in range(board.ROWS):  # 9 rows
            for j in range(board.COLS):  # 8 columns
                # Calculate cell boundaries more precisely
                x1 = int(j * (width / board.COLS))
                y1 = int(i * (height / board.ROWS))
                x2 = int((j + 1) * (width / board.COLS))
                y2 = int((i + 1) * (height / board.ROWS))
                
                # Extract region with margins
                # Use larger margin horizontally (for left/right) and smaller margin vertically (for top/bottom)
                h_margin = int(width * 0.02)  # 1% of width for horizontal margins
                v_margin = 4  # Small fixed margin for vertical
                cell = board_image[
                    y1 + v_margin:y2 - v_margin,
                    x1 + h_margin:x2 - h_margin
                ]
                
                # Save the cell
                cv2.imwrite(f'{cells_folder}/cell_{i}_{j}.png', cell)
                
                # Skip if cell is mostly blue background
                if is_mostly_blue(cell):
                    continue
                
                # Process the cell to get the letter
                letter = process_cell(cell, i, j, cells_folder)
                if letter:
                    # For now, treat all blocks as single blocks
                    # TODO: Detect vertical/horizontal stacks
                    block = Block(
                        type=BlockType.SINGLE,
                        letters=[letter],
                        position=(i, j)
                    )
                    board.add_block(block)
        
        return board
    
    # Handle other game modes as before...
    elif game_version.startswith("ANAGRAM"):
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
