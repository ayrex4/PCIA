import PIL.Image
import cv2
import json
import re
from google import genai
from utils.logger import get_logger

logger = get_logger("VisionAI")

class VisionAI:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)
        # Note: Using flash-lite here is perfectly fine for Vision tasks!
        self.model_name = 'gemini-3.1-flash-lite'
        self.fallback_model_name = 'gemini-2.5-flash'

    def _generate_with_resilience(self, contents, max_retries=2):
        delay = 1.5
        for attempt in range(max_retries + 1):
            try:
                return self.client.models.generate_content(model=self.model_name, contents=contents)
            except Exception as e:
                is_unavailable = "503" in str(e) or "UNAVAILABLE" in str(e).upper()
                if is_unavailable and attempt < max_retries:
                    logger.warning(f"Vision model unavailable, retrying in {delay:.1f}s (attempt {attempt+1}/{max_retries})...")
                    import time
                    time.sleep(delay)
                    delay *= 2
                    continue
                if is_unavailable:
                    logger.warning(f"Primary vision model still unavailable. Falling back to {self.fallback_model_name}.")
                    return self.client.models.generate_content(model=self.fallback_model_name, contents=contents)
                raise

    def _clean_model_text(self, text):
        if not text:
            return ""
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
            cleaned = cleaned.replace("```", "").strip()
        return cleaned

    def _looks_like_prompt_echo(self, answer):
        if not answer:
            return True
        lowered = answer.lower()
        suspicious_markers = [
            "look at this screenshot",
            "reply only with the answer text",
            "instructions:",
            "here is text physically scraped",
        ]
        return any(marker in lowered for marker in suspicious_markers)

    def extract_information(self, cv_image, question):
        """Extracts text/data from the screen."""
        try:
            rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
            pil_image = PIL.Image.fromarray(rgb_image)
            prompt = f"""
            You are reading a messaging app screenshot.
            TASK: {question}
            Return ONLY the final extracted answer text.
            Do not repeat the task, instructions, or screenshot description.
            If uncertain, return exactly: NOT_FOUND
            """
            response = self._generate_with_resilience([prompt, pil_image])
            answer = self._clean_model_text(response.text)
            if self._looks_like_prompt_echo(answer):
                logger.warning("Vision extraction looked like prompt echo.")
                return "NOT_FOUND"
            return answer
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
            
            response = self._generate_with_resilience([prompt, pil_image])
            
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

    def get_ui_element_description(self, cv_image, x, y):
        """
        Asks Gemini to describe the UI element at the given (x, y) coordinates.
        Used for Semantic Skill Compilation.
        """
        try:
            # Draw a prominent red circle around the clicked area to guide the model
            annotated_image = cv_image.copy()
            cv2.circle(annotated_image, (x, y), radius=40, color=(0, 0, 255), thickness=4)
            cv2.circle(annotated_image, (x, y), radius=4, color=(0, 0, 255), thickness=-1)
            
            rgb_image = cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB)
            pil_image = PIL.Image.fromarray(rgb_image)
            
            prompt = f"""
            I have drawn a red circle around a specific UI element on this screenshot (at coordinates x:{x}, y:{y}).
            What is the name or purpose of this exact UI element? 
            Reply with ONLY a short, concise description (max 5 words) that could be used to find it again later.
            Examples: "Send button", "Search bar", "Paperclip icon", "Settings gear".
            """
            
            response = self._generate_with_resilience([prompt, pil_image])
            return self._clean_model_text(response.text).replace('"', '')
        except Exception as e:
            logger.error(f"Failed to describe UI element: {e}")
            return "unknown button"

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
            response = self._generate_with_resilience(prompt)
            answer = self._clean_model_text(response.text)
            if self._looks_like_prompt_echo(answer):
                logger.warning("Text analysis looked like prompt echo.")
                return "NOT_FOUND"
            return answer
        except Exception as e:
            logger.error(f"Text Analysis Failed: {e}")
            return "Failed to extract data."