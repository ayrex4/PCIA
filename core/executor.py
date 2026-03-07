import pyautogui
import time
import cv2
import numpy as np
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

    def type_text(self, text, press_enter=False):
        logger.info(f"Typing text: '{text}'")
        pyautogui.write(text, interval=0.01) 
        if press_enter:
            pyautogui.press('enter')
            logger.info("Pressed ENTER.")
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
        pyautogui.moveTo(x, y, duration=0.3)
        pyautogui.click()

    def wait_for_ui_to_settle(self, timeout=10, threshold=500):
        logger.info("Waiting for UI to settle (Visual Wait)...")
        start_time = time.time()
        
        last_screen = self.screen.capture_full()
        last_gray = cv2.cvtColor(last_screen, cv2.COLOR_BGR2GRAY)
        
        while time.time() - start_time < timeout:
            time.sleep(0.5)
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