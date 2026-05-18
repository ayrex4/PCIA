import json
import cv2
import PIL.Image
import time
from google import genai
from utils.logger import get_logger

logger = get_logger("TaskPlanner")

class TaskPlanner:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)
        self.model_name = 'gemini-3.1-flash-lite'
        self.fallback_model_name = 'gemini-3-flash-preview'

    def _generate_with_resilience(self, contents, max_retries=2):
        """Retry on temporary service failures, then fallback to a secondary model."""
        delay = 1.5
        for attempt in range(max_retries + 1):
            try:
                return self.client.models.generate_content(model=self.model_name, contents=contents)
            except Exception as e:
                is_unavailable = "503" in str(e) or "UNAVAILABLE" in str(e).upper()
                if is_unavailable and attempt < max_retries:
                    logger.warning(f"Planner model unavailable, retrying in {delay:.1f}s (attempt {attempt+1}/{max_retries})...")
                    time.sleep(delay)
                    delay *= 2
                    continue
                if is_unavailable:
                    logger.warning(f"Primary model still unavailable. Falling back to {self.fallback_model_name}.")
                    return self.client.models.generate_content(model=self.fallback_model_name, contents=contents)
                raise

    def _parse_json_response(self, response_text):
        raw_text = response_text.strip()
        if raw_text.startswith("```json"): raw_text = raw_text[7:-3].strip()
        elif raw_text.startswith("```"): raw_text = raw_text[3:-3].strip()
        try:
            return json.loads(raw_text)
        except Exception:
            return {}

    def generate_plan(self, user_prompt, system_context, learning_history, user_preferences=None):
        logger.info(f"Asking Gemini to plan task: {user_prompt}")
        user_preferences = user_preferences or {}
        
        system_instructions = f"""
        You are the System Architect of PCIA. Output ONLY valid JSON.
        
        CURRENT ENVIRONMENT: {system_context}
        PAST MISTAKES (Do not repeat these): {learning_history}
        USER PREFERENCES: {json.dumps({k: v for k, v in user_preferences.items() if k != 'personal_memory'})}
        
        PERSONAL MEMORY (Facts the user has explicitly told you to remember. ALWAYS use these when relevant):
        {user_preferences.get('personal_memory', 'No personal memories saved yet.')}
        
        ACTIONS (You MUST use the exact key 'intent'):
        1. Type (clipboard-based, works for any charset): {{"intent": "type", "target_value": "text", "press_enter": true}}
        1b. Safe Type (keyboard simulation, NEVER touches clipboard): {{"intent": "safe_type", "target_value": "text", "press_enter": false}}
        2. Press Key: {{"intent": "press_key", "target_value": "win/enter/tab"}}
        3. Hotkey: {{"intent": "hotkey", "target_value": ["ctrl", "f"]}}
        4. Wait for UI: {{"intent": "wait_for_ui", "target_value": 10}}
        5. Wait Hard (Time): {{"intent": "wait_hard", "target_value": 3}}
        6. Scroll: {{"intent": "scroll", "target_value": -500}}
        7. Drag: {{"intent": "drag", "target_value": "100,100,500,500"}}
        8. Click Text: {{"intent": "click_text", "target_value": "Exact Link Text"}}
        9. Click Coordinates: {{"intent": "click_coordinates", "target_value": "160, 510"}}
        10. Extract (Visual): {{"intent": "extract", "target_value": "What to extract from the current screen"}}
        11. Right Click Vision: {{"intent": "right_click_vision", "target_value": "The element to right click"}}
        12. Replan: {{"intent": "replan", "target_value": "What to look for on a dynamic screen"}}
        13. Download Image: {{"intent": "download_image", "target_value": {{"query":"porsche 911 wallpaper 4k","min_width":1920,"min_height":1080}}}}
        14. Attach Last Downloaded Image: {{"intent": "attach_last_downloaded_image", "target_value": ""}}
        15. Run Command: {{"intent": "run_command", "target_value": "powershell -command \\"New-Item -ItemType Directory -Path ~/Desktop/namesFSO\\""}}

        
        KNOWN PATTERNS (Learned Skills):
        {json.dumps(user_preferences.get('learned_skills_data', {}), indent=2)}
        
        RULES:
        - If the user asks for a task that matches a KNOWN PATTERN, you MUST use the exact sequence of intents from that pattern.
        - CRITICAL: You must IMPROVISE and MODIFY the `target_value`s in the pattern to match the user's CURRENT request. For example, if the pattern types "porsche" but the user asked for "nissan", change the type intent to "nissan".
        - Never repeat a task from PAST MISTAKES. Try a different approach.
        - Prefer "extract" for reading on-screen content. Use physical_scrape only as legacy fallback.
        - If PAST MISTAKES mention physical_scrape/clipboard/KeyboardInterrupt, avoid physical_scrape-first strategies.
        - In that case prefer visual strategies: replan -> click_text/click_vision -> extract via on-screen context.
        - PRIORITY: When the goal is to find visible text in UI, prefer OCR-compatible steps first (click_text, ctrl+f search flows) before vision-only steps.
        - To search INSIDE an app (like WhatsApp...): ALWAYS use hotkey ["ctrl", "f"].
        - To play a song in Spotify: press_key(win) -> safe_type("spotify") -> press_key(enter) -> wait_hard(7) [Spotify is slow to launch, always wait at least 7s] -> hotkey(["ctrl", "k"]) -> wait_hard(2) -> type(song or artist name) -> wait_hard(3) [search results need time to load] -> hotkey(["shift", "enter"]) to immediately play. NEVER use plain press_key(enter) in Spotify — that only selects, it does NOT play.
        - For text discovery in chats/docs, use iterative loop: search/click_text -> wait_for_ui -> if not found then scroll -> wait_for_ui -> search/click_text again.
        - For message-check tasks (e.g., WhatsApp unread/new message): after opening chat, if target text is not visible, scroll DOWN and retry text search before fallback.
        - For general web search: press_key(win) -> type(chrome) -> press_key(enter) -> wait_for_ui(2) -> hotkey(ctrl, l) -> type(https://www.google.com/search?q=QUERY) -> press_key(enter) -> wait_for_ui(3) -> extract/replan.
        CLIPBOARD PROTECTION RULE (CRITICAL — NEVER BREAK THIS):
        - The 'type' intent uses clipboard paste (Ctrl+V) internally. This OVERWRITES whatever image or file is in the clipboard.
        - After copying an image from the browser (step: click_text(Copy image)), the image lives ONLY in the clipboard.
        - Any 'type' intent fired after that point will DESTROY the image before you can paste it.
        - SOLUTION: After copying an image, switch ALL subsequent text-typing steps to 'safe_type' until the paste step.
          'safe_type' simulates keyboard keypresses and NEVER touches the clipboard.
        - 'safe_type' limitation: ASCII characters only. For WhatsApp navigation (contact names in Latin script), it is always safe.
        - For non-ASCII or URL typing BEFORE the image is copied, 'type' is fine.

        FAST IMAGE SEARCH & SEND WORKFLOW (Browser Native, CLIPBOARD-SAFE):
        If the user wants to find a photo and send it via WhatsApp:
          1. press_key(win) -> safe_type("chrome") -> press_key(enter) -> wait_hard(3)
          2. hotkey(ctrl, l) -> type("https://www.google.com/search?as_st=y&as_q=YOUR_QUERY_HERE&udm=2&imgsz=svga") -> press_key(enter) -> wait_hard(5)
             [NOTE: URL typing uses 'type' (clipboard) here because no image is in clipboard yet]
          3. click_coordinates(160, 510) -> wait_hard(4)
          4. press_key(tab) -> press_key(tab) -> press_key(tab) -> press_key(tab)
          5. press_key(apps) -> wait_hard(1)
          6. click_text("Copy image") OR click_text("Copier l'image") -> wait_hard(1)
             [IMAGE IS NOW IN CLIPBOARD. From this point forward, ONLY use safe_type, press_key, hotkey, click_text, click_coordinates]
          7. press_key(win) -> safe_type("whatsapp") -> press_key(enter) -> wait_hard(4)
          8. hotkey(ctrl, f) -> safe_type("CONTACT_NAME") -> wait_hard(2) -> press_key(enter) -> wait_hard(2)
          9. hotkey(ctrl, v) -> wait_hard(2) -> press_key(enter)
             [This Ctrl+V pastes the IMAGE, not text, because safe_type was used for all navigation]
        - Use download_image ONLY if user explicitly asks to "download to disk" or "save to folder".
        - To type extracted data, use {{MEMORY}} in the target_value.
        - When drafting messages, NEVER use markdown like asterisks (*) or hashes (#). Use simple conversational text.
        - For OS-level tasks (creating folders, managing files), ALWAYS use "run_command" instead of UI automation.
        - KNOWN DIRECTORIES: Desktop is 'C:\\Users\\ayman\\OneDrive\\Bureau', Documents is 'C:\\Users\\ayman\\OneDrive\\Documents', Images is 'C:\\Users\\ayman\\OneDrive\\Images'. Use these exact absolute paths in your commands.
        
        CRITICAL RULES FOR CHATS & MESSAGES (WHATSAPP):
        - If user asks about "message/messages/chat" without naming an app, default to USER PREFERENCES.default_messaging_app.
        - For message checks, always ensure app context first: focus(default app) OR open via win search + enter before in-app search.
        - To find an unread chat, do not guess coordinates. Use:
          {{"intent": "replan", "target_value": "Click the chat with the unread message indicator (badge/dot/count)."}}
        - If OCR cannot identify unread indicators, allow vision fallback via sub-plan using click_vision.
        - To read a message in an opened chat, use:
          {{"intent": "extract", "target_value": "Read the most recent message received in this chat."}}
        - After selecting a contact from WhatsApp search results, confirm chat open with: {{"intent":"press_key","target_value":"enter"}} then wait_for_ui(2) before extract.
        - Once extracted, content is available in {{MEMORY}} for follow-up typing.
        - To reply, use:
          {{"intent": "type", "target_value": "your reply with {{MEMORY}}", "press_enter": true}}
        - If unread badge or target chat is not found, replan with alternate phrasing and retry before failing.
        
        FORMAT: {{"thought_process": "Explain logic here", "tasks":[ ... ]}}
        """

        try:
            response = self._generate_with_resilience([system_instructions, user_prompt])
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
            AVAILABLE ACTIONS: click_text, click_vision, extract, download_image, attach_last_downloaded_image, middle_click_text, type, press_key, hotkey, scroll, wait_for_ui.
            
            CRITICAL FORMATTING RULES:
            1. You MUST use the exact keys "intent" and "target_value" for every task.
            2. NEVER use the keys "action", "task", "action_input", or "parameters". If you do, the system will crash.
            3. CORRECT EXAMPLE: {"intent": "click_text", "target_value": "Some text"}
            4. INCORRECT EXAMPLE: {"action": "click_text", "text": "Some text"}
            
            RULES FOR CLICKING:
            1. To click a link or name, find its exact visible text and use "click_text".
            2. If you don't see what you need, use "scroll" with -500 (down) to find it.
            3. For text-heavy UIs, prioritize click_text (OCR-first). Use click_vision only when text is unavailable.
            4. For chat/message checks, after each scroll step, add wait_for_ui then retry click_text/search flow.
            
            RULES FOR CHATS:
            - If looking for an unread message badge/indicator, prefer "click_vision" because OCR may miss non-text badges.
            - Example: {"intent": "click_vision", "target_value": "The chat contact with an unread notification badge"}
            - If unread indicators are not found, return a fallback sequence: wait_for_ui -> scroll (small step) -> click_vision retry.
            
            FORMAT: JSON object with "thought_process" and "tasks" array.
            """
            
            prompt = f"SUB-GOAL: {sub_goal}. Generate JSON tasks."
            response = self._generate_with_resilience([system_instructions, prompt, pil_image])
            
            plan_data = self._parse_json_response(response.text)
            if isinstance(plan_data, list): return plan_data
            logger.info(f"MINI-BRAIN THOUGHTS: {plan_data.get('thought_process', 'No thoughts provided')}")
            return plan_data.get('tasks',[])
        except Exception as e:
            logger.error(f"Mini-Brain failed: {e}")
            return[]