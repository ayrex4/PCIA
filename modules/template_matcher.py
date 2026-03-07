import cv2
import numpy as np
from utils.logger import get_logger

logger = get_logger("TemplateMatcher")

class TemplateMatcher:
    def __init__(self, threshold=0.8):
        self.threshold = threshold

    def find_icon(self, screen_image, template_path):
        logger.info(f"Looking for template: {template_path}")
        template = cv2.imread(template_path, cv2.IMREAD_COLOR)
        if template is None:
            logger.error(f"Could not load template at {template_path}")
            return None

        result = cv2.matchTemplate(screen_image, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= self.threshold:
            # max_loc is the top-left corner
            h, w = template.shape[:2]
            center_x = max_loc[0] + (w // 2)
            center_y = max_loc[1] + (h // 2)
            logger.info(f"Icon found with confidence {max_val:.2f} at ({center_x}, {center_y})")
            return (center_x, center_y)
        
        logger.warning(f"Icon not found. Max confidence: {max_val:.2f} (Threshold: {self.threshold})")
        return None