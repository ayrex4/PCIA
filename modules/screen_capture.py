import mss
import numpy as np
import cv2
from utils.logger import get_logger

logger = get_logger("ScreenCapture")

class ScreenCapture:
    def __init__(self):
        self.sct = mss.mss()

    def capture_full(self):
        """Captures the full screen and returns an OpenCV image array."""
        logger.debug("Capturing full screen...")
        monitor = self.sct.monitors[1] # Primary monitor
        screenshot = self.sct.grab(monitor)
        
        # Convert to numpy array for OpenCV
        img = np.array(screenshot)
        
        # Convert BGRA to BGR (Fixed typo here)
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    def capture_region(self, region):
        """Captures a specific region: (left, top, width, height)"""
        screenshot = self.sct.grab(region)
        img = np.array(screenshot)
        
        # Convert BGRA to BGR (Fixed typo here)
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)