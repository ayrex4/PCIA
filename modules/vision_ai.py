import PIL.Image
import cv2
import json
from google import genai
from utils.logger import get_logger

logger = get_logger("VisionAI")

class VisionAI:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)
        self.model_name = 'gemini-flash-lite-latest' 

    def extract_information(self, cv_image, question):
        """Extracts text/data from the screen."""
        try:
            rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
            pil_image = PIL.Image.fromarray(rgb_image)
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[f"Look at this screenshot. {question}. Reply ONLY with the answer text.", pil_image]
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Extraction Failed: {e}")
            return "Error"

    def get_coordinates(self, cv_image, description):
        """
        Asks Gemini to find the (x, y) coordinates of a UI element described by text.
        Returns: (x, y) tuple or None
        """
        logger.info(f"👀 Vision AI looking for: '{description}'")
        
        try:
            rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
            pil_image = PIL.Image.fromarray(rgb_image)
            
            # We ask Gemini to return JSON coordinates
            prompt = f"""
            Analyze this UI screenshot. Find the element described as: "{description}".
            Return the exact center coordinates (x, y) of this element.
            
            RESPONSE FORMAT: JSON only. Example: {{"x": 500, "y": 300}}
            If not found, return {{"error": "not found"}}
            """
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt, pil_image]
            )
            
            # Clean response
            text = response.text.strip()
            if text.startswith("```json"): text = text[7:-3]
            elif text.startswith("```"): text = text[3:-3]
            
            data = json.loads(text)
            
            if "error" in data:
                logger.warning(f"Vision AI could not find '{description}'")
                return None
                
            return (int(data['x']), int(data['y']))

        except Exception as e:
            logger.error(f"Vision AI Coordinate Error: {e}")
            return None