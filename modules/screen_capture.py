import mss
import numpy as np
import cv2
from utils.logger import get_logger

logger = get_logger("ScreenCapture")

class ScreenCapture:
    def __init__(self):
        # mss keeps thread-local handles; create a fresh context per capture call
        # so this class works from both CLI and GUI worker threads.
        pass

    def capture_full(self):
        """Captures the full screen and returns an OpenCV image array."""
        logger.debug("Capturing full screen...")
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # Primary monitor
            screenshot = sct.grab(monitor)
        
        # Convert to numpy array for OpenCV
        img = np.array(screenshot)
        
        # Convert BGRA to BGR (Fixed typo here)
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    def capture_region(self, region):
        """Captures a specific region: (left, top, width, height)"""
        with mss.mss() as sct:
            screenshot = sct.grab(region)
        img = np.array(screenshot)
        
        # Convert BGRA to BGR (Fixed typo here)
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)