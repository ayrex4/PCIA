import json
import cv2
import PIL.Image
from google import genai
from utils.logger import get_logger

logger = get_logger("TaskPlanner")

class TaskPlanner:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)
        self.model_name = 'gemini-3.1-flash-lite-preview' 

    def _parse_json_response(self, response_text):
        raw_text = response_text.strip()
        if raw_text.startswith("```json"): raw_text = raw_text[7:-3].strip()
        elif raw_text.startswith("```"): raw_text = raw_text[3:-3].strip()
        try:
            return json.loads(raw_text)
        except Exception:
            return {}

    def generate_plan(self, user_prompt, system_context, learning_history):
        logger.info(f"Asking Gemini to plan task: {user_prompt}")
        
        system_instructions = f"""
        You are the System Architect of PCIA. Output ONLY valid JSON.
        
        CURRENT ENVIRONMENT: {system_context}
        PAST MISTAKES (Do not repeat these): {learning_history}
        
        ACTIONS (You MUST use the exact key 'intent'):
        1. Type: {{"intent": "type", "target_value": "text", "press_enter": true}}
        2. Press Key: {{"intent": "press_key", "target_value": "win/enter/tab"}}
        3. Hotkey: {{"intent": "hotkey", "target_value": ["ctrl", "f"]}}
        4. Wait: {{"intent": "wait_for_ui", "target_value": 10}}
        5. Scroll: {{"intent": "scroll", "target_value": -500}}
        6. Drag: {{"intent": "drag", "target_value": "100,100,500,500"}}
        7. Click Text: {{"intent": "click_text", "target_value": "Exact Link Text"}}
        8. Physical Scrape: {{"intent": "physical_scrape", "target_value": "What to extract"}}
        9. Replan: {{"intent": "replan", "target_value": "What to look for on a dynamic screen"}}
        
        RULES:
        - Never repeat a task from PAST MISTAKES. Try a different approach.
        - For web search: press_key(win) -> type(chrome) -> type(query) -> replan(to find link) -> physical_scrape.
        - To type extracted data, use {{MEMORY}} in the target_value.
        RULES:
        - Never repeat a task from PAST MISTAKES. Try a different approach.
        - To search INSIDE an app (like WhatsApp...): ALWAYS use hotkey ["ctrl", "f"] ; (like spotify): ALWAYS use hotkey ["ctrl", "k"]  -> type(Name) -> wait_for_ui(3) -> press_key(enter).
        - For web search: press_key(win) -> type(chrome) -> type(query) -> wait_for_ui -> replan(to find link) -> physical_scrape.
        - To type extracted data, use {{MEMORY}} in the target_value.
        - When drafting messages, NEVER use markdown like asterisks (*) or hashes (#). Use simple conversational text.
        
        FORMAT: {{"thought_process": "Explain logic here", "tasks":[ ... ]}}
        """

        try:
            response = self.client.models.generate_content(model=self.model_name, contents=[system_instructions, user_prompt])
            plan_data = self._parse_json_response(response.text)
            if isinstance(plan_data, list): return plan_data
            logger.info(f"PLANNER THOUGHTS: {plan_data.get('thought_process', 'No thoughts provided')}")
            return plan_data.get('tasks',[])
        except Exception as e:
            logger.error(f"Planner error: {e}")
            return[]

    def generate_sub_plan(self, sub_goal, cv_image):
        logger.info(f"Mini-Brain analyzing screen for: {sub_goal}")
        try:
            rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
            pil_image = PIL.Image.fromarray(rgb_image)
            
            system_instructions = """
            You are the Tactical Mini-Brain. Look at the screenshot and generate tasks.
            AVAILABLE ACTIONS: click_text, middle_click_text, type, press_key, hotkey, scroll, wait_for_ui.
            
            CRITICAL FORMATTING RULES:
            1. You MUST use the exact keys "intent" and "target_value" for every task.
            2. NEVER use the keys "action", "task", "action_input", or "parameters". If you do, the system will crash.
            3. CORRECT EXAMPLE: {"intent": "click_text", "target_value": "Some text"}
            4. INCORRECT EXAMPLE: {"action": "click_text", "text": "Some text"}
            
            RULES FOR CLICKING:
            1. To click a link or name, find its exact visible text and use "click_text".
            2. If you don't see what you need, use "scroll" with -500 (down) to find it.
            
            FORMAT: JSON object with "thought_process" and "tasks" array.
            """
            
            prompt = f"SUB-GOAL: {sub_goal}. Generate JSON tasks."
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[system_instructions, prompt, pil_image]
            )
            
            plan_data = self._parse_json_response(response.text)
            if isinstance(plan_data, list): return plan_data
            logger.info(f"MINI-BRAIN THOUGHTS: {plan_data.get('thought_process', 'No thoughts provided')}")
            return plan_data.get('tasks',[])
        except Exception as e:
            logger.error(f"Mini-Brain failed: {e}")
            return[]