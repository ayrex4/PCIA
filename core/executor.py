import pyautogui
import time
import cv2
import numpy as np
import os
from utils.logger import get_logger

logger = get_logger("Executor")

class Executor:
    def __init__(self, screen_capture, ocr, template_matcher, vision_ai, os_controller):
        self.screen = screen_capture
        self.ocr = ocr
        self.template = template_matcher
        self.vision = vision_ai
        self.os = os_controller
        self.memory = {}
        # Runtime-tunable interaction speed defaults.
        self.mouse_move_duration = float(os.getenv("PCIA_MOUSE_MOVE_DURATION", "0.1"))
        self.ui_settle_poll_interval = float(os.getenv("PCIA_UI_SETTLE_POLL_INTERVAL", "0.2"))

    def type_text(self, text, press_enter=False, safe_typing=False):
        """
        Type text into the focused field.

        safe_typing=True  → uses pyautogui.write() (keyboard simulation).
                            Does NOT touch the clipboard. Use this whenever
                            an image/file is sitting in the clipboard and
                            must not be overwritten.
                            Limitation: ASCII-only. Falls back to clipboard
                            for non-ASCII characters.
        safe_typing=False (default) → clipboard paste via Ctrl+V. Works for
                            any character set and avoids AZERTY/QWERTY
                            layout issues. Overwrites clipboard.
        """
        logger.info(f"Typing text (safe={safe_typing}): '{text}'")
        text = str(text)

        if safe_typing:
            # Check if the text can be typed directly (ASCII printable only)
            try:
                text.encode('ascii')
                is_ascii = True
            except UnicodeEncodeError:
                is_ascii = False

            if is_ascii:
                # pyautogui.write() types char by char — safe, no clipboard touch
                pyautogui.write(text, interval=0.02)
            else:
                # Non-ASCII fallback: still needs clipboard (unavoidable)
                import pyperclip
                logger.warning("safe_typing: non-ASCII text, falling back to clipboard paste.")
                pyperclip.copy(text)
                time.sleep(0.1)
                pyautogui.hotkey('ctrl', 'v')
        else:
            import pyperclip
            # Using clipboard paste prevents keyboard layout mangling of URLs/symbols
            pyperclip.copy(text)
            time.sleep(0.1)
            pyautogui.hotkey('ctrl', 'v')

        time.sleep(0.1)
        if press_enter:
            pyautogui.press('enter')
            logger.info("Pressed ENTER.")
        return True

    def run_skill(self, skill_name):
        logger.info(f"Replaying skill: {skill_name}")
        skill_file = os.path.join("data", "skills", f"{skill_name.lower().replace(' ', '_')}.json")
        if not os.path.exists(skill_file):
            logger.error(f"Skill file not found: {skill_file}")
            return False
            
        import json
        with open(skill_file, "r") as f:
            data = json.load(f)
            
        events = data.get("events", [])
        if not events: return False
        
        last_time = 0
        for event in events:
            # Replay with realistic timing (capped at 2 seconds max between actions)
            delay = min(event["time"] - last_time, 2.0)
            if delay > 0:
                time.sleep(delay)
            last_time = event["time"]
            
            try:
                if event["type"] == "mouse_click":
                    pyautogui.moveTo(event["x"], event["y"], duration=0.2)
                    pyautogui.click(button=event.get("button", "left"))
                elif event["type"] == "mouse_scroll":
                    pyautogui.scroll(event["delta"] * 120)
                elif event["type"] == "key_press":
                    key = event["key"]
                    if len(key) == 1: pyautogui.write(key)
                    else: pyautogui.press(key)
            except Exception as e:
                logger.error(f"Error replaying event {event}: {e}")
                
        return True

    def execute(self, task, strategies):
        for strategy in strategies:
            logger.info(f"--- Attempting execution using: {strategy.upper()} ---")
            success = False
            
            # Capture 'Before' state
            state_before = self.screen.capture_full()
            
            if strategy == "os_control":
                app = task['target_value']['app']
                element = task['target_value']['element']
                success = self.os.click_element(app, element)
            else:
                coords = None
                if strategy == "ocr":
                    coords = self.ocr.find_text_coordinates(state_before, task['target_value'])
                elif strategy == "template_matching":
                    coords = self.template.find_icon(state_before, task['target_value'])
                
                # 🔥 FIXED: Use get_coordinates for Vision Strategy
                elif strategy == "vision" or strategy == "vision_ai":
                    coords = self.vision.get_coordinates(state_before, task['target_value'])

                if coords:
                    self._click_coordinates(coords[0], coords[1])
                    success = True

            if success:
                # We skip verification for now on generic clicks to keep it fast
                # You can re-enable verify_action(state_before) here if desired
                return True
            else:
                logger.warning(f"Strategy {strategy} failed to find target.")

        logger.error("All strategies exhausted. Task Failed.")
        return False

    def _click_coordinates(self, x, y):
        logger.info(f"Moving mouse to ({x}, {y}) and clicking.")
        pyautogui.moveTo(x, y, duration=self.mouse_move_duration)
        pyautogui.click()

    def wait_for_ui_to_settle(self, timeout=10, threshold=5000):
        logger.info("Waiting for UI to settle (Visual Wait)...")
        start_time = time.time()
        
        last_screen = self.screen.capture_full()
        last_gray = cv2.cvtColor(last_screen, cv2.COLOR_BGR2GRAY)
        
        while time.time() - start_time < timeout:
            time.sleep(self.ui_settle_poll_interval)
            current_screen = self.screen.capture_full()
            current_gray = cv2.cvtColor(current_screen, cv2.COLOR_BGR2GRAY)
            
            diff = cv2.absdiff(last_gray, current_gray)
            _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
            changed_pixels = np.count_nonzero(thresh)
            
            logger.debug(f"UI Motion: {changed_pixels} pixels changing.")
            
            if changed_pixels < threshold:
                logger.info("UI has settled. Proceeding.")
                return True
            
            last_gray = current_gray
            
        logger.warning(f"UI did not settle within {timeout}s. Proceeding anyway.")
        return False

    def verify_action(self, state_before):
        logger.info("Verifying screen state change...")
        time.sleep(0.5) 
        state_after = self.screen.capture_full()
        diff = cv2.absdiff(state_before, state_after)
        gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        changed_pixels = np.count_nonzero(gray_diff > 25) 
        
        logger.debug(f"Verification Check: {changed_pixels} pixels changed on screen.")
        if changed_pixels > 5000:
            logger.info("State change detected! Action was effective.")
            return True
        else:
            logger.warning("No significant visual change detected.")
            return False