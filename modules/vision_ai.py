import PIL.Image
import cv2
import json
from google import genai
from utils.logger import get_logger

logger = get_logger("VisionAI")

class VisionAI:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)
        # Note: Using flash-lite here is perfectly fine for Vision tasks!
        self.model_name = 'gemini-3.1-flash-lite-preview' 

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
        # REMOVED THE EMOJI THAT CAUSED THE WINDOWS CRASH!
        logger.info(f"Vision AI looking for: '{description}'") 
        
        try:
            rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
            pil_image = PIL.Image.fromarray(rgb_image)
            
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
        
    def analyze_text(self, text_content, instructions):
        """Reads a massive wall of text (like a scraped website) and extracts what we need."""
        logger.info("Asking Gemini to analyze scraped text...")
        try:
            prompt = f"""
            Here is text physically scraped from a website:
            ---
            {text_content[:15000]} # Limit to 15k characters to avoid token limits
            ---
            INSTRUCTIONS: {instructions}. 
            Return ONLY the extracted answer, cleanly formatted.
            """
            response = self.client.models.generate_content(
                model='gemini-2.5-flash', # Use the smart model for text analysis
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Text Analysis Failed: {e}")
            return "Failed to extract data."