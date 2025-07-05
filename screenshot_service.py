import base64
import io
import os
from datetime import datetime
from PIL import ImageGrab, Image
import mss
from typing import Optional, Tuple, List
import json

class ScreenshotService:
    """
    Service for capturing screenshots and encoding them to base64.
    Supports multiple monitors and different capture methods.
    """
    
    def __init__(self, debug_folder: str = "debug_screenshots"):
        """Initialize the screenshot service."""
        self.sct = mss.mss()
        self.debug_folder = debug_folder
        self.debug_enabled = False
        
        # Create debug folder if it doesn't exist
        if not os.path.exists(self.debug_folder):
            os.makedirs(self.debug_folder)
    
    def get_monitors(self) -> List[dict]:
        """
        Get information about all available monitors.
        
        Returns:
            List[dict]: List of monitor information dictionaries
        """
        return self.sct.monitors
    
    def capture_monitor(self, monitor_index: int = 0, quality: int = 85) -> str:
        """
        Capture screenshot of a specific monitor and return as base64 string.
        
        Args:
            monitor_index (int): Monitor index (0 for primary, 1+ for additional monitors)
            quality (int): JPEG quality (1-100, higher = better quality)
        
        Returns:
            str: Base64 encoded screenshot
        
        Raises:
            IndexError: If monitor_index is invalid
            Exception: If screenshot capture fails
        """
        try:
            monitors = self.get_monitors()
            
            if monitor_index >= len(monitors):
                raise IndexError(f"Monitor index {monitor_index} not found. Available monitors: {len(monitors)}")
            
            # Use monitor 0 for all monitors, or specific monitor index
            if monitor_index == 0:
                # Capture all monitors
                monitor_config = monitors[0]  # This captures all monitors
            else:
                monitor_config = monitors[monitor_index]
            
            # Capture the screenshot
            screenshot = self.sct.grab(monitor_config)
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
            # Save debug image if enabled
            if self.debug_enabled:
                saved_path = self._save_debug_image(img, f"monitor_{monitor_index}")
                print(f"Debug: Screenshot saved to {saved_path}")
            
            # Convert to base64
            return self._image_to_base64(img, quality)
            
        except Exception as e:
            raise Exception(f"Failed to capture screenshot: {str(e)}")
    
    def capture_primary_monitor(self, quality: int = 85) -> str:
        """
        Capture screenshot of the primary monitor.
        
        Args:
            quality (int): JPEG quality (1-100)
        
        Returns:
            str: Base64 encoded screenshot
        """
        try:
            # Use PIL's ImageGrab for primary monitor (more reliable on Windows)
            img = ImageGrab.grab()
            
            # Save debug image if enabled
            if self.debug_enabled:
                saved_path = self._save_debug_image(img, "primary_monitor")
                print(f"Debug: Primary monitor screenshot saved to {saved_path}")
            
            return self._image_to_base64(img, quality)
        except Exception as e:
            raise Exception(f"Failed to capture primary monitor: {str(e)}")
    
    def capture_region(self, bbox: Tuple[int, int, int, int], quality: int = 85) -> str:
        """
        Capture screenshot of a specific region.
        
        Args:
            bbox (Tuple[int, int, int, int]): Bounding box (left, top, right, bottom)
            quality (int): JPEG quality (1-100)
        
        Returns:
            str: Base64 encoded screenshot
        """
        try:
            img = ImageGrab.grab(bbox)
            return self._image_to_base64(img, quality)
        except Exception as e:
            raise Exception(f"Failed to capture region: {str(e)}")
    
    def _image_to_base64(self, img: Image.Image, quality: int = 85) -> str:
        """
        Convert PIL Image to base64 string.
        
        Args:
            img (Image.Image): PIL Image object
            quality (int): JPEG quality (1-100)
        
        Returns:
            str: Base64 encoded image
        """
        # Create a BytesIO buffer
        buffer = io.BytesIO()
        
        # Save image to buffer as JPEG
        img.save(buffer, format='JPEG', quality=quality, optimize=True)
        
        # Get the buffer content and encode to base64
        buffer.seek(0)
        img_bytes = buffer.getvalue()
        base64_string = base64.b64encode(img_bytes).decode('utf-8')
        
        return base64_string
    
    def get_monitor_info(self) -> str:
        """
        Get formatted information about all monitors.
        
        Returns:
            str: JSON formatted monitor information
        """
        monitors = self.get_monitors()
        info = []
        
        for i, monitor in enumerate(monitors):
            if i == 0:
                info.append({
                    "index": i,
                    "name": "All Monitors",
                    "dimensions": f"{monitor['width']}x{monitor['height']}",
                    "position": f"({monitor['left']}, {monitor['top']})"
                })
            else:
                info.append({
                    "index": i,
                    "name": f"Monitor {i}",
                    "dimensions": f"{monitor['width']}x{monitor['height']}",
                    "position": f"({monitor['left']}, {monitor['top']})"
                })
        
        return json.dumps(info, indent=2)
    
    def enable_debug(self, enabled: bool = True):
        """
        Enable or disable debug mode for saving screenshots to files.
        
        Args:
            enabled (bool): Whether to enable debug mode
        """
        self.debug_enabled = enabled
        if enabled:
            print(f"Debug mode enabled. Screenshots will be saved to: {self.debug_folder}")
        else:
            print("Debug mode disabled.")
    
    def _save_debug_image(self, img: Image.Image, prefix: str = "screenshot") -> str:
        """
        Save image to debug folder with timestamp.
        
        Args:
            img (Image.Image): PIL Image to save
            prefix (str): Filename prefix
            
        Returns:
            str: Path to saved file
        """
        if not self.debug_enabled:
            return ""
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
        filename = f"{prefix}_{timestamp}.jpg"
        filepath = os.path.join(self.debug_folder, filename)
        
        img.save(filepath, format='JPEG', quality=85, optimize=True)
        return filepath

# Example usage and testing
async def test_screenshot_service():
    """Test the screenshot service."""
    service = ScreenshotService()
    
    print("Available monitors:")
    print(service.get_monitor_info())
    
    try:
        # Enable debug mode
        service.enable_debug(True)
        
        # Capture primary monitor
        base64_img = service.capture_primary_monitor(quality=70)
        print(f"Screenshot captured successfully. Base64 length: {len(base64_img)}")
        
        # Test with different monitors if available
        monitors = service.get_monitors()
        if len(monitors) > 1:
            print(f"Testing monitor 1 capture...")
            base64_img_monitor1 = service.capture_monitor(1, quality=70)
            print(f"Monitor 1 screenshot captured. Base64 length: {len(base64_img_monitor1)}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_screenshot_service()) 