import json
from google import genai
from utils.logger import get_logger

logger = get_logger("TaskPlanner")

class TaskPlanner:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)
        self.model_name = 'gemini-flash-lite-latest' 

    def generate_plan(self, user_prompt):
        logger.info(f"Asking Gemini to plan task: '{user_prompt}'")
        
        system_instructions = """
        You are the Brain of PCIA, an AI desktop automation agent.
        Your job is to translate user requests into a strict JSON array of tasks.
        
        AVAILABLE ACTIONS (intents):
        1. Click text: {"intent": "Click [Name]", "target_type": "text", "target_value": "Exact Text on Screen"}
        2. Click icon: {"intent": "Click [Name]", "target_type": "icon", "target_value": "image_name.png"}
        3. Type text: {"intent": "type", "target_value": "text", "press_enter": false/true}
        4. Press key: {"intent": "press_key", "target_value": "enter/down/up/space/esc/win/tab"}
        5. Hotkey: {"intent": "hotkey", "target_value":["ctrl", "f"]}
        6. Smart Wait: {"intent": "wait_for_ui", "target_value": 10}  # Use this AFTER opening apps or loading pages.
        7. Extract: {"intent": "extract", "target_value": "Question"}
        8. Click Vision: {"intent": "click_vision", "target_type": "vision", "target_value": "Description of element (e.g. 'Green Play Button', 'Search Bar')"}
        
        🔥🔥 IMPROVISATION & KNOWLEDGE RULES:
        1. Open apps using Windows Search (Win -> Type -> Enter).
        2. If you know a reliable hotkey (like Ctrl+A), use it via {"intent": "hotkey"}.
        3. IF YOU DO NOT KNOW A SHORTCUT, simply click the element using "click_vision".
           Example: {"intent": "click_vision", "target_type": "vision", "target_value": "The search bar at the top"}
        4. DO NOT assume specific image filenames exist. Use "click_vision" instead of "click_icon".

        CRITICAL OS RULES:
        1. When opening an app or a webpage, ALWAYS use "wait_for_ui" (value 10) immediately after. Do not guess sleep times.
        2. To play a song in Spotify:
           - Open Spotify -> wait_for_ui
           - Hotkey ["ctrl", "k"] -> Type Song Name -> Enter
           - wait_for_ui (wait for search results)
           - Click icon: "spotify_play.png" (The green play button)        3. To scroll, use "press_key" -> "pagedown".

        EXAMPLE (User: "Play Phonk on Spotify"):
        [
            {"intent": "press_key", "target_value": "win"},
            {"intent": "type", "target_value": "Spotify", "press_enter": true},
            {"intent": "sleep", "target_value": 4},
            {"intent": "hotkey", "target_value": ["ctrl", "k"]}, 
            {"intent": "type", "target_value": "Phonk", "press_enter": true},
            {"intent": "sleep", "target_value": 2},
            {"intent": "press_key", "target_value": "tab"}, 
            {"intent": "press_key", "target_value": "enter"}
        ]

        RULES:
        - NEVER return anything except a raw JSON array.
        """

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[system_instructions, f"USER REQUEST: {user_prompt}"]
            )
            
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:-3].strip()
            elif raw_text.startswith("```"):
                raw_text = raw_text[3:-3].strip()
                
            task_chain = json.loads(raw_text)
            logger.info(f"Successfully generated a plan with {len(task_chain)} steps.")
            return task_chain
            
        except Exception as e:
            logger.error(f"Failed to generate plan: {e}")
            return None