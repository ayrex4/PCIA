import cv2
import pytesseract
import re
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
        
        target_words = target_text.lower().split()
        if not target_words:
            return None
            
        n_words = len(target_words)
        for i in range(len(data['text']) - n_words + 1):
            if not data['text'][i].strip():
                continue
                
            match = True
            for j in range(n_words):
                if target_words[j] not in data['text'][i+j].lower():
                    match = False
                    break
            
            if match:
                x1 = data['left'][i]
                y1 = data['top'][i]
                x2 = data['left'][i+n_words-1] + data['width'][i+n_words-1]
                y2 = max(data['top'][i+j] + data['height'][i+j] for j in range(n_words))
                
                center_x = x1 + (x2 - x1) // 2
                center_y = y1 + (y2 - y1) // 2
                logger.info(f"Found '{target_text}' at ({center_x}, {center_y})")
                return (center_x, center_y)
                
        logger.warning(f"Text '{target_text}' not found.")
        return None

    def extract_all_text(self, image, max_chars=12000):
        """
        Runs OCR on the full image and returns cleaned text.
        Useful for screen-level extraction before using Vision fallback.
        """
        try:
            processed_img = self.preprocess_image(image)
            raw_text = pytesseract.image_to_string(processed_img)
            cleaned = re.sub(r"\r\n?", "\n", raw_text or "")
            cleaned = re.sub(r"[ \t]+", " ", cleaned)
            cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
            if len(cleaned) > max_chars:
                cleaned = cleaned[:max_chars]
            return cleaned
        except Exception as e:
            logger.error(f"OCR full-text extraction failed: {e}")
            return ""

    def get_text_at_coordinate(self, image, x, y, margin=10):
        """Returns the text found at the specified coordinate, or None."""
        try:
            processed_img = self.preprocess_image(image)
            data = pytesseract.image_to_data(processed_img, output_type=pytesseract.Output.DICT)
            
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                if not text: continue
                
                left = data['left'][i]
                top = data['top'][i]
                width = data['width'][i]
                height = data['height'][i]
                
                if (left - margin <= x <= left + width + margin) and (top - margin <= y <= top + height + margin):
                    # Found text! We might want to grab the whole line/block for better context, 
                    # but the exact word is safest for 'click_text'.
                    return text
            return None
        except Exception as e:
            logger.error(f"OCR text at coordinate failed: {e}")
            return None