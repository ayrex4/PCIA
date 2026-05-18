import time
import json
import os
import threading
from pathlib import Path
from utils.logger import get_logger
from modules.screen_capture import ScreenCapture
from modules.vision_ai import VisionAI
from modules.ocr import OCRDetector

logger = get_logger("SkillLearner")

class SkillLearner:
    def __init__(self, skills_dir="data/skills", api_key=None):
        self.skills_dir = Path(skills_dir)
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self.recording = False
        self.events = []
        self.start_time = 0
        
        self.screen = ScreenCapture()
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        import keyboard
        import mouse
        self.keyboard = keyboard
        self.mouse = mouse

    def get_available_skills(self):
        skills = []
        if not self.skills_dir.exists(): return skills
        for f in self.skills_dir.glob("*.json"):
            skills.append(f.stem)
        return skills

    def _mouse_event_callback(self, event):
        if not self.recording: return
        import mouse
        t = time.time() - self.start_time
        
        if isinstance(event, mouse.ButtonEvent) and event.event_type == 'down':
            x, y = mouse.get_position()
            # Capture screenshot immediately
            try:
                screenshot = self.screen.capture_full()
            except:
                screenshot = None
                
            self.events.append({
                "type": "mouse_click",
                "time": t,
                "x": x,
                "y": y,
                "button": event.button,
                "screenshot": screenshot
            })
        elif isinstance(event, mouse.WheelEvent):
            self.events.append({
                "type": "mouse_scroll",
                "time": t,
                "delta": event.delta
            })

    def _keyboard_event_callback(self, event):
        if not self.recording: return
        import keyboard
        t = time.time() - self.start_time
        
        if event.name in ['ctrl', 'shift', 'esc']: return
        
        if event.event_type == 'down':
            self.events.append({
                "type": "key_press",
                "time": t,
                "key": event.name
            })

    def start_recording(self):
        logger.info("Starting Semantic Skill Recording...")
        self.events = []
        self.recording = True
        self.start_time = time.time()
        
        self.mouse.hook(self._mouse_event_callback)
        self.keyboard.hook(self._keyboard_event_callback)

    def stop_recording(self, skill_name):
        logger.info(f"Stopping recording. Entering Semantic Compilation Phase...")
        self.recording = False
        time.sleep(0.5) 
        
        self.mouse.unhook(self._mouse_event_callback)
        self.keyboard.unhook(self._keyboard_event_callback)
        
        if not self.events:
            logger.warning("No events recorded!")
            return False
            
        print("\n[COMPILING SKILL] Analyzing your actions using Vision AI. This takes a moment...")
        vision = VisionAI(self.api_key)
        
        compiled_tasks = []
        last_time = 0
        current_text_buffer = ""
        
        for event in self.events:
            # If the human paused for more than 1 second, tell the agent to wait for UI
            delay = event["time"] - last_time
            if delay >= 1.0:
                if current_text_buffer:
                    compiled_tasks.append({"intent": "type", "target_value": current_text_buffer})
                    current_text_buffer = ""
                # Add wait_for_ui based on human pause
                compiled_tasks.append({"intent": "wait_for_ui", "target_value": min(int(delay) + 1, 10)})
                
            last_time = event["time"]

            if event["type"] == "key_press":
                key = event["key"]
                
                # Remap keyboard module names to pyautogui compatible names
                if "windows" in key or "win" in key: key = "win"
                elif key == "enter": key = "enter"
                elif key == "backspace": key = "backspace"
                
                if len(key) == 1 or key == "space":
                    current_text_buffer += " " if key == "space" else key
                else:
                    if current_text_buffer:
                        compiled_tasks.append({"intent": "type", "target_value": current_text_buffer})
                        current_text_buffer = ""
                    compiled_tasks.append({"intent": "press_key", "target_value": key})
                    
            elif event["type"] == "mouse_click":
                if current_text_buffer:
                    compiled_tasks.append({"intent": "type", "target_value": current_text_buffer})
                    current_text_buffer = ""
                    
                screenshot = event.pop("screenshot", None)
                if screenshot is not None:
                    # 1. Try OCR first for perfectly accurate text clicks
                    ocr = OCRDetector()
                    text_at_click = ocr.get_text_at_coordinate(screenshot, event["x"], event["y"])
                    
                    if text_at_click:
                        compiled_tasks.append({"intent": "click_text", "target_value": text_at_click})
                    else:
                        # 2. Fall back to Vision AI to describe the icon/element
                        desc = vision.get_ui_element_description(screenshot, event["x"], event["y"])
                        compiled_tasks.append({"intent": "click_vision", "target_value": desc})
                else:
                    compiled_tasks.append({"intent": "click_vision", "target_value": "fallback absolute coordinate"})
                    
            elif event["type"] == "mouse_scroll":
                if current_text_buffer:
                    compiled_tasks.append({"intent": "type", "target_value": current_text_buffer})
                    current_text_buffer = ""
                compiled_tasks.append({"intent": "scroll", "target_value": event["delta"] * 120})

        if current_text_buffer:
            compiled_tasks.append({"intent": "type", "target_value": current_text_buffer})

        file_path = self.skills_dir / f"{skill_name.lower().replace(' ', '_')}.json"
        with open(file_path, "w") as f:
            json.dump({
                "skill_name": skill_name,
                "created_at": time.time(),
                "semantic_plan": compiled_tasks
            }, f, indent=4)
            
        logger.info(f"Semantic Skill '{skill_name}' compiled successfully!")
        print(f"\n[SUCCESS] I learned how to do '{skill_name}'!")
        for task in compiled_tasks:
            print(f"  -> {task['intent']}: {task['target_value']}")
            
        return True
