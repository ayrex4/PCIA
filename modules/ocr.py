import cv2
import pytesseract
from utils.logger import get_logger

logger = get_logger("OCR_Module")

class OCRDetector:
    def __init__(self, tesseract_cmd=None):
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    def preprocess_image(self, image):
        """Grayscale and thresholding for better OCR accuracy."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Apply binary thresholding
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        return thresh

    def find_text_coordinates(self, image, target_text):
        """Returns the (x, y) center of the target text, or None."""
        logger.info(f"Scanning screen for text: '{target_text}'")
        processed_img = self.preprocess_image(image)
        
        # Get bounding box data
        data = pytesseract.image_to_data(processed_img, output_type=pytesseract.Output.DICT)
        
        for i in range(len(data['text'])):
            if target_text.lower() in data['text'][i].lower():
                x = data['left'][i]
                y = data['top'][i]
                w = data['width'][i]
                h = data['height'][i]
                
                center_x = x + (w // 2)
                center_y = y + (h // 2)
                
                # CHANGED: logger.success to logger.info
                logger.info(f"Found '{target_text}' at ({center_x}, {center_y})")
                return (center_x, center_y)
                
        logger.warning(f"Text '{target_text}' not found.")
        return None