import Quartz
from src.config.config import IPHONE_WINDOW_KEYWORDS

# Cache for window bounds
_window_cache = None

def find_iphone_window(force_refresh=False):
    """Find the iPhone window and return its bounds."""
    global _window_cache
    
    # Return cached window bounds if available and not forcing refresh
    if not force_refresh and _window_cache is not None:
        return _window_cache
    
    # Get all windows
    window_list = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly,
        Quartz.kCGNullWindowID
    )
    
    # Look for iPhone window
    for window in window_list:
        window_name = window.get('kCGWindowName', '')
        window_owner = window.get('kCGWindowOwnerName', '')
        
        # Check if window name or owner contains any of our keywords
        if any(keyword.lower() in window_name.lower() or 
               keyword.lower() in window_owner.lower() 
               for keyword in IPHONE_WINDOW_KEYWORDS):
            
            # Get window bounds
            bounds = window.get('kCGWindowBounds', {})
            x = bounds.get('X', 0)
            y = bounds.get('Y', 0)
            width = bounds.get('Width', 0)
            height = bounds.get('Height', 0)
            
            # Only print window info when forcing refresh
            if force_refresh:
                print(f"Found iPhone window: '{window_name}' by '{window_owner}'")
                print(f"Window bounds: x={x}, y={y}, width={width}, height={height}")
            
            _window_cache = {
                'x': x,
                'y': y,
                'width': width,
                'height': height
            }
            return _window_cache
    
    if force_refresh:
        print("No iPhone window found")
    _window_cache = None
    return None 