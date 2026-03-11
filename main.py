import time
import os
import re
import pyautogui
import pyperclip
import json
from dotenv import load_dotenv

# --- IMPORTS ---
from utils.logger import get_logger
from utils.learning_journal import log_failure, get_learning_history
from modules.screen_capture import ScreenCapture
from modules.ocr import OCRDetector
from modules.template_matcher import TemplateMatcher
from modules.vision_ai import VisionAI
from modules.os_controller import OSController
from modules.system_monitor import SystemObserver

from core.decision_engine import DecisionEngine
from core.executor import Executor
from core.planner import TaskPlanner

# --- SETUP ---
pyautogui.FAILSAFE = False
load_dotenv()
logger = get_logger("PCIA_Main")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 

if not GEMINI_API_KEY:
    logger.error("CRITICAL: GEMINI_API_KEY not found in .env file!")
    exit()

def initialize_agent():
    logger.info("Initializing PCIA Modules...")
    screen = ScreenCapture()
    tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    ocr = OCRDetector(tesseract_cmd=tesseract_path)
    template = TemplateMatcher(threshold=0.8)
    vision = VisionAI(api_key=GEMINI_API_KEY)
    os_ctrl = OSController()
    
    decision = DecisionEngine()
    executor = Executor(screen, ocr, template, vision, os_ctrl)
    planner = TaskPlanner(api_key=GEMINI_API_KEY)
    observer = SystemObserver()
    
    return decision, executor, planner, observer

def run_task_chain(task_chain, decision, executor, planner):
    logger.info(f"=== Starting Task Chain ({len(task_chain)} steps) ===")
    
    for i, task in enumerate(task_chain):
        intent = task.get('intent', 'UNKNOWN')
        val = task.get('target_value', '')
        logger.info(f"--- Step {i+1}: {intent} ---")
        
        try:
            # 1. Type with Memory Injection
            if intent == "type":
                if "MEMORY" in str(val):
                    extracted_data = executor.memory.get("last_extracted", "[No data found]")
                    val = re.sub(r'\{MEMORY[^}]*\}', extracted_data, str(val))
                executor.type_text(val, press_enter=task.get('press_enter', False))
                time.sleep(0.5) 
                
            # 2. Window Focus
            elif intent == "focus":
                executor.os.focus_app(val)
                time.sleep(1.0)

            # 3. Keys and Hotkeys
            elif intent == "press_key":
                pyautogui.press(val)
                time.sleep(0.5) 
                
            elif intent == "hotkey":
                pyautogui.hotkey(*val)
                time.sleep(0.5) 
                
            # 4. Scroll (Safe integer handling)
            elif intent == "scroll":
                try: 
                    scroll_amount = int(val)
                except: 
                    scroll_amount = -500 
                pyautogui.moveTo(960, 540) # Ensure focus before scrolling
                pyautogui.scroll(scroll_amount)
                time.sleep(1.0)
                
            # 5. Drag Ability
            elif intent == "drag":
                logger.info(f"Dragging coordinates: {val}")
                coords = [int(x.strip()) for x in val.split(',')]
                pyautogui.dragTo(coords[0], coords[1], coords[2], coords[3], duration=0.8)

            # 6. Smart Wait (Safe integer handling)
            elif intent == "wait_for_ui":
                try: 
                    timeout_val = int(val)
                except: 
                    timeout_val = 10
                executor.wait_for_ui_to_settle(timeout=timeout_val)

            # 7. Physical Scrape
            elif intent == "physical_scrape":
                logger.info("Executing Physical Scrape (Ctrl+A, Ctrl+C)...")
                time.sleep(1.0)
                pyautogui.click(960, 540) 
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.5)
                pyautogui.hotkey('ctrl', 'c')
                time.sleep(0.5)
                # 🔥 FIX: Press ESC instead of clicking a random coordinate to unselect text
                pyautogui.press('esc') 
                
                scraped_text = pyperclip.paste()
                extracted_info = executor.vision.analyze_text(scraped_text, val)
                executor.memory["last_extracted"] = extracted_info
                logger.info("Data extracted and saved to memory.")

            # 8. Replan (Mini-Brain Recursion)
            elif intent == "replan":
                logger.info(f"Triggering Mini-Brain: {val}")
                time.sleep(1.0) 
                current_screen = executor.screen.capture_full()
                sub_tasks = planner.generate_sub_plan(val, current_screen)
                if sub_tasks:
                    logger.info("Sub-plan generated. Executing...")
                    run_task_chain(sub_tasks, decision, executor, planner)

            # 9. Click Text (OCR)
            elif intent == "click_text":
                current_screen = executor.screen.capture_full()
                coords = executor.ocr.find_text_coordinates(current_screen, val)
                if coords:
                    executor._click_coordinates(coords[0], coords[1])
                else:
                    raise Exception(f"OCR could not find text: '{val}'")
            
            # 10. Click Vision
            elif intent == "click_vision":
                current_screen = executor.screen.capture_full()
                coords = executor.vision.get_coordinates(current_screen, val)
                if coords:
                    executor._click_coordinates(coords[0], coords[1])
                else:
                    raise Exception(f"Vision AI could not find: '{val}'")

            # 11. Fallback for old strategies
            else:
                strategies = decision.select_strategy(task)
                success = executor.execute(task, strategies)
                if not success:
                    raise Exception(f"Executor failed to execute intent: {intent}")

        # 🔥 SELF-LEARNER IN ACTION: Log detailed failures
        except KeyError as ke:
            error_msg = f"Missing JSON key: {ke}. You MUST use 'intent' and 'target_value' as the keys."
            logger.error(f"Step {i+1} Failed: {error_msg}")
            log_failure(task, error_msg)
            logger.warning("Formatting error logged to Learning Journal. Halting chain.")
            break
        except Exception as e:
            logger.error(f"Step {i+1} Failed: {e}")
            log_failure(task, str(e))
            logger.warning("Failure recorded in Learning Journal. Halting current chain.")
            break
        
    logger.info("=== Task Chain Complete ===")

if __name__ == "__main__":
    decision_engine, agent_executor, planner, observer = initialize_agent()
    
    # Get system context and history ONCE at startup
    system_context = observer.get_context()
    learning_history = get_learning_history()

    print("\n" + "="*50)
    print("Welcome to PCIA v0.1 - The Cognitive Agent")
    print(f"[{system_context}]")
    print("="*50)
    
    user_prompt = input("\nWhat would you like me to do? \n> ")

    logger.info("Generating Main Task Plan...")
    dynamic_chain = planner.generate_plan(user_prompt, system_context, learning_history)

    if dynamic_chain:
        print("\n--- GENERATED PLAN ---")
        for step in dynamic_chain:
            print(f"- {step.get('intent')} -> {step.get('target_value')}")
        print("----------------------\n")
        
        logger.info("Starting execution in 3 seconds... hands off!")
        time.sleep(3)
        run_task_chain(dynamic_chain, decision_engine, agent_executor, planner)
    else:
        logger.error("Could not understand the request or API failed.")