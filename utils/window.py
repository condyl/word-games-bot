import Quartz
from config import IPHONE_WINDOW_KEYWORDS

def find_iphone_window():
    """Get the iPhone mirroring window position and dimensions."""
    windows = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
        Quartz.kCGNullWindowID
    )
    
    for window in windows:
        title = window.get(Quartz.kCGWindowName, 'Unknown')
        owner = window.get(Quartz.kCGWindowOwnerName, 'Unknown')
        
        if any(keyword.lower() in str(title).lower() or 
               keyword.lower() in str(owner).lower() 
               for keyword in IPHONE_WINDOW_KEYWORDS):
            bounds = window.get(Quartz.kCGWindowBounds)
            return {
                'x': bounds['X'],
                'y': bounds['Y'],
                'width': bounds['Width'],
                'height': bounds['Height']
            }
    return None 