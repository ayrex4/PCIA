import time
import os
import pyautogui
from dotenv import load_dotenv  # 🔥 NEW: Library to read .env files
from utils.logger import get_logger
from modules.screen_capture import ScreenCapture
from modules.ocr import OCRDetector
from modules.template_matcher import TemplateMatcher
from modules.vision_ai import VisionAI
from modules.os_controller import OSController
from core.decision_engine import DecisionEngine
from core.executor import Executor
from core.planner import TaskPlanner

# Load environment variables from .env file
load_dotenv()

# Setup
logger = get_logger("PCIA_Main")
# 🔥 NEW: Get key securely. If missing, it returns None.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 

if not GEMINI_API_KEY:
    logger.error("CRITICAL: GEMINI_API_KEY not found in .env file!")
    exit()

def initialize_agent():
    logger.info("Initializing PCIA Modules...")
    screen = ScreenCapture()
    # Ensure this path is correct for your PC
    tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    ocr = OCRDetector(tesseract_cmd=tesseract_path)
    template = TemplateMatcher(threshold=0.8)
    vision = VisionAI(api_key=GEMINI_API_KEY)
    os_ctrl = OSController()
    
    decision = DecisionEngine()
    executor = Executor(screen, ocr, template, vision, os_ctrl)
    planner = TaskPlanner(api_key=GEMINI_API_KEY)
    
    return decision, executor, planner

def run_task_chain(task_chain, decision, executor):
    logger.info(f"=== Starting Task Chain ({len(task_chain)} steps) ===")
    
    for i, task in enumerate(task_chain):
        logger.info(f"--- Step {i+1}: {task['intent']} ---")
        
        # 1. Handle Typing Actions
        if task['intent'] == "type":
            text_to_type = task['target_value']
            if "{MEMORY}" in text_to_type:
                extracted_data = executor.memory.get("last_extracted", "[Nothing extracted]")
                text_to_type = text_to_type.replace("{MEMORY}", extracted_data)
            executor.type_text(text_to_type, press_enter=task.get('press_enter', False))
            time.sleep(0.5) 
            continue

        # 2. Handle Single Key Presses
        elif task['intent'] == "press_key":
            logger.info(f"Pressing key: '{task['target_value']}'")
            pyautogui.press(task['target_value'])
            time.sleep(0.5) 
            continue
            
        # 3. Handle Shortcuts
        elif task['intent'] == "hotkey":
            logger.info(f"Pressing shortcut: {task['target_value']}")
            pyautogui.hotkey(*task['target_value'])
            time.sleep(0.5) 
            continue
            
        # 4. Handle Scrolling
        elif task['intent'] == "scroll":
            logger.info(f"Scrolling by {task['target_value']} units")
            pyautogui.scroll(int(task['target_value']))
            time.sleep(1.0)
            continue
            
        # 5. Smart Visual Wait
        elif task['intent'] == "wait_for_ui":
            executor.wait_for_ui_to_settle(timeout=int(task['target_value']))
            continue

        # 6. Handle Sleep
        elif task['intent'] == "sleep":
            logger.info(f"Waiting for {task['target_value']} seconds...")
            time.sleep(float(task['target_value']))
            continue
            
        # 7. Handle Screen Extraction
        elif task['intent'] == "extract":
            logger.info("Taking screenshot for Vision AI extraction...")
            time.sleep(1.0) 
            current_screen = executor.screen.capture_full()
            extracted_text = executor.vision.extract_information(current_screen, task['target_value'])
            executor.memory["last_extracted"] = extracted_text
            continue
        
        # 8. 🔥 SPECIAL CASE: Click Vision (Directly call Vision AI)
        elif task['intent'] == "click_vision":
            logger.info(f"Attempting Vision Click on: {task['target_value']}")
            current_screen = executor.screen.capture_full()
            coords = executor.vision.get_coordinates(current_screen, task['target_value'])
            if coords:
                executor._click_coordinates(coords[0], coords[1])
                # Optional: Verify action here
            continue

        # 9. Normal Detection (OCR, Icons)
        strategies = decision.select_strategy(task)
        success = executor.execute(task, strategies)
        
        if not success:
            logger.error(f"Chain broken at Step {i+1}. Stopping execution.")
            break
            
    logger.info("=== Task Chain Complete ===")

if __name__ == "__main__":
    decision_engine, agent_executor, planner = initialize_agent()

    print("\n" + "="*50)
    print("🤖 Welcome to PCIA v0.1 - The Cognitive Agent")
    print("="*50)
    
    user_prompt = input("\nWhat would you like me to do on your PC? \n> ")

    logger.info("Generating task plan...")
    dynamic_chain = planner.generate_plan(user_prompt)

    if dynamic_chain:
        print("\n--- GENERATED PLAN ---")
        for step in dynamic_chain:
            print(f"- {step['intent']} -> {step['target_value']}")
        print("----------------------\n")
        
        logger.info("Starting execution in 3 seconds... hands off!")
        time.sleep(3)
        
        run_task_chain(dynamic_chain, decision_engine, agent_executor)
    else:
        logger.error("Could not understand the request or API failed.")