import time
import os
import re
import pyautogui
import pyperclip
import json
import warnings
from dotenv import load_dotenv

# Suppress noisy Pydantic/Google GenAI deprecation warnings in the terminal
warnings.filterwarnings("ignore", category=DeprecationWarning)

# --- IMPORTS ---
from utils.logger import get_logger
from utils.learning_journal import (
    log_failure,
    get_recent_failure_summary,
    log_run_history,
    set_user_preference,
    get_user_preference,
)
from utils.memory_store import (
    remember,
    recall_all,
    forget,
    get_memory_summary,
    parse_memory_command,
)
from modules.screen_capture import ScreenCapture
from modules.ocr import OCRDetector
from modules.template_matcher import TemplateMatcher
from modules.vision_ai import VisionAI
from modules.os_controller import OSController
from modules.system_monitor import SystemObserver
from modules.image_fetcher import ImageFetcher

from core.decision_engine import DecisionEngine
from core.executor import Executor
from core.planner import TaskPlanner

# --- SETUP ---
pyautogui.FAILSAFE = True
load_dotenv()
logger = get_logger("PCIA_Main")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 
FAST_ACTION_PAUSE_SECONDS = float(os.getenv("PCIA_FAST_ACTION_PAUSE_SECONDS", "0.2"))
USE_CLIPBOARD_SCRAPE = os.getenv("PCIA_USE_CLIPBOARD_SCRAPE", "0").strip() in {"1", "true", "yes"}
USE_OCR_FIRST_EXTRACTION = os.getenv("PCIA_USE_OCR_FIRST_EXTRACTION", "1").strip() in {"1", "true", "yes"}
VISION_CHAT_FALLBACK = os.getenv("PCIA_VISION_CHAT_FALLBACK", "0").strip() in {"1", "true", "yes"}
USER_PROFILE_PATH = "data/user_profile.json"

def _is_chat_extraction_request(instruction):
    text = str(instruction or "").lower()
    return any(token in text for token in ["message", "messages", "chat", "whatsapp", "unread", "reply"])

def load_user_profile():
    defaults = {
        "default_messaging_app": "whatsapp",
        "default_result_style": "contact_quote",
        "message_output_template": "{contact} said to you: \"{message}\"",
        "contacts": {
            "sister": "",
            "brother": "",
            "mom": "",
            "dad": "",
        },
        "automation": {
            "use_ocr_first_extraction": True,
            "use_clipboard_scrape": False,
            "vision_chat_fallback": False,
        },
    }
    if not os.path.exists(USER_PROFILE_PATH):
        return defaults
    try:
        with open(USER_PROFILE_PATH, "r") as f:
            loaded = json.load(f)
            if isinstance(loaded, dict):
                merged = defaults.copy()
                merged.update(loaded)
                if not isinstance(merged.get("contacts"), dict):
                    merged["contacts"] = defaults["contacts"]
                if not isinstance(merged.get("automation"), dict):
                    merged["automation"] = defaults["automation"]
                return merged
    except (json.JSONDecodeError, OSError):
        pass
    return defaults

if not GEMINI_API_KEY:
    logger.error("CRITICAL: GEMINI_API_KEY not found in .env file!")
    exit()

def initialize_agent():
    logger.info("Initializing PCIA Modules...")
    screen = ScreenCapture()
    tesseract_path = os.getenv("TESSERACT_CMD_PATH", r'C:\Program Files\Tesseract-OCR\tesseract.exe')
    ocr = OCRDetector(tesseract_cmd=tesseract_path)
    template = TemplateMatcher(threshold=0.8)
    vision = VisionAI(api_key=GEMINI_API_KEY)
    os_ctrl = OSController()
    image_fetcher = ImageFetcher()
    
    decision = DecisionEngine()
    executor = Executor(screen, ocr, template, vision, os_ctrl)
    planner = TaskPlanner(api_key=GEMINI_API_KEY)
    observer = SystemObserver()
    
    return decision, executor, planner, observer, image_fetcher

def run_task_chain(task_chain, decision, executor, planner, image_fetcher, allow_recovery=True):
    logger.info(f"=== Starting Task Chain ({len(task_chain)} steps) ===")
    chain_success = True
    
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
                safe = task.get('safe_typing', False)
                executor.type_text(val, press_enter=task.get('press_enter', False), safe_typing=safe)
                time.sleep(FAST_ACTION_PAUSE_SECONDS)

            # 1b. Safe Type — never overwrites clipboard (use when image/file is in clipboard)
            elif intent == "safe_type":
                if "MEMORY" in str(val):
                    extracted_data = executor.memory.get("last_extracted", "[No data found]")
                    val = re.sub(r'\{MEMORY[^}]*\}', extracted_data, str(val))
                executor.type_text(val, press_enter=task.get('press_enter', False), safe_typing=True)
                time.sleep(FAST_ACTION_PAUSE_SECONDS)
                
            # 2. Window Focus
            elif intent == "focus":
                executor.os.focus_app(val)
                time.sleep(1.0)


            elif intent == "press_key":
                pyautogui.press(val)
                time.sleep(FAST_ACTION_PAUSE_SECONDS)
                
            elif intent == "hotkey":
                pyautogui.hotkey(*val)
                time.sleep(FAST_ACTION_PAUSE_SECONDS)
                
            # 4. Scroll (Safe integer handling)
            elif intent == "scroll":
                try: 
                    scroll_amount = int(val)
                except: 
                    scroll_amount = -500 
                screen_width, screen_height = pyautogui.size()
                pyautogui.moveTo(screen_width // 2, screen_height // 2) # Ensure focus before scrolling
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
                
            # 6b. Hard Wait (Deterministic sleep)
            elif intent == "wait_hard":
                try: timeout_val = float(val)
                except: timeout_val = 3.0
                logger.info(f"Hard waiting for {timeout_val} seconds...")
                time.sleep(timeout_val)

            # 7. Physical Scrape
            elif intent == "physical_scrape":
                logger.info("Executing data extraction...")
                extracted_info = None
                scrape_interrupted = False
                is_chat_request = _is_chat_extraction_request(val)
                if USE_CLIPBOARD_SCRAPE:
                    # Optional legacy mode: use Ctrl+A/C only when explicitly enabled.
                    try:
                        pyperclip.copy("")
                    except Exception:
                        pass
                    try:
                        time.sleep(1.0)
                        screen_width, screen_height = pyautogui.size()
                        pyautogui.click(screen_width // 2, screen_height // 2)
                        pyautogui.hotkey('ctrl', 'a')
                        time.sleep(0.4)
                        pyautogui.hotkey('ctrl', 'c')
                        time.sleep(0.4)
                    except KeyboardInterrupt:
                        logger.warning("Physical scrape interrupted (likely terminal Ctrl+C conflict). Falling back to visual extraction.")
                        scrape_interrupted = True
                    finally:
                        try:
                            pyautogui.press('esc')
                        except Exception:
                            pass

                if USE_CLIPBOARD_SCRAPE:
                    scraped_text = pyperclip.paste().strip()
                else:
                    scraped_text = ""

                if scraped_text and not scrape_interrupted:
                    # Clipboard content is already text; for chat checks keep it OCR/text-first.
                    extracted_info = scraped_text if is_chat_request else executor.vision.analyze_text(scraped_text, val)
                else:
                    current_screen = executor.screen.capture_full()
                    ocr_text = executor.ocr.extract_all_text(current_screen) if USE_OCR_FIRST_EXTRACTION else ""
                    if ocr_text:
                        extracted_info = ocr_text if is_chat_request else executor.vision.analyze_text(ocr_text, val)
                    if (
                        (not extracted_info or str(extracted_info).strip().lower() in {"error", "none", "", "not_found"})
                        and (not is_chat_request or VISION_CHAT_FALLBACK)
                    ):
                        extracted_info = executor.vision.extract_information(current_screen, val)

                extracted_normalized = str(extracted_info).strip().lower() if extracted_info is not None else ""
                if not extracted_info or extracted_normalized in {"error", "none", "", "not_found"}:
                    raise Exception("Could not extract usable information from clipboard or screenshot.")

                executor.memory["last_extracted"] = extracted_info
                logger.info(f"Data extracted and saved to memory: {extracted_info}")

            # 8. Direct visual extraction (preferred over clipboard scraping)
            elif intent == "extract":
                current_screen = executor.screen.capture_full()
                extracted_info = None
                is_chat_request = _is_chat_extraction_request(val)
                if USE_OCR_FIRST_EXTRACTION:
                    ocr_text = executor.ocr.extract_all_text(current_screen)
                    if ocr_text:
                        extracted_info = ocr_text if is_chat_request else executor.vision.analyze_text(ocr_text, val)
                if (
                    (not extracted_info or str(extracted_info).strip().lower() in {"error", "none", "", "not_found"})
                    and (not is_chat_request or VISION_CHAT_FALLBACK)
                ):
                    extracted_info = executor.vision.extract_information(current_screen, val)
                extracted_normalized = str(extracted_info).strip().lower() if extracted_info is not None else ""
                if not extracted_info or extracted_normalized in {"error", "none", "", "not_found"}:
                    raise Exception("Could not extract usable information from screen.")
                executor.memory["last_extracted"] = extracted_info
                logger.info(f"Data extracted and saved to memory: {extracted_info}")

            # 9. Replan (Mini-Brain Recursion)
            elif intent == "replan":
                logger.info(f"Triggering Mini-Brain: {val}")
                time.sleep(1.0) 
                current_screen = executor.screen.capture_full()
                sub_tasks = planner.generate_sub_plan(val, current_screen)
                if sub_tasks:
                    logger.info("Sub-plan generated. Executing...")
                    sub_ok = run_task_chain(
                        sub_tasks,
                        decision,
                        executor,
                        planner,
                        image_fetcher,
                        allow_recovery=False,
                    )
                    chain_success = chain_success and sub_ok

            # 10. Click Text (OCR)
            elif intent == "click_text":
                current_screen = executor.screen.capture_full()
                coords = executor.ocr.find_text_coordinates(current_screen, val)
                if coords:
                    executor._click_coordinates(coords[0], coords[1])
                else:
                    raise Exception(f"OCR could not find text: '{val}'")
            
            # 11. Click Vision
            elif intent == "click_vision":
                current_screen = executor.screen.capture_full()
                coords = executor.vision.get_coordinates(current_screen, val)
                if coords:
                    executor._click_coordinates(coords[0], coords[1])
                else:
                    raise Exception(f"Vision AI could not find: '{val}'")
                    
            # 11b. Click Coordinates (Blind click)
            elif intent == "click_coordinates":
                coords = [int(x.strip()) for x in val.split(',')]
                logger.info(f"Blind clicking coordinates: {coords}")
                executor._click_coordinates(coords[0], coords[1])
                    
            # 11b. Right Click Vision (for context menus)
            elif intent == "right_click_vision":
                current_screen = executor.screen.capture_full()
                coords = executor.vision.get_coordinates(current_screen, val)
                if coords:
                    logger.info(f"Right-clicking at {coords}")
                    pyautogui.moveTo(coords[0], coords[1], duration=0.2)
                    pyautogui.click(button='right')
                else:
                    raise Exception(f"Vision AI could not find: '{val}' for right click")

            # 12. Download high-quality image from web by query
            elif intent == "download_image":
                # 🔥 FIX: If the Mini-Brain accidentally sends a stringified dictionary, parse it!
                if isinstance(val, str) and val.strip().startswith('{'):
                    try:
                        val = json.loads(val)
                    except Exception:
                        pass
                
                if isinstance(val, dict):
                    query = str(val.get("query", "")).strip()
                    min_width = int(val.get("min_width", 1200))
                    min_height = int(val.get("min_height", 800))
                else:
                    query = str(val).strip()
                    min_width = 1200
                    min_height = 800
                    
                if not query:
                    raise Exception("download_image requires a non-empty query.")
                    
                result = image_fetcher.download_best_image(
                    query=query,
                    min_width=min_width,
                    min_height=min_height,
                )
                if not result:
                    raise Exception(f"Could not download high-quality image for query: '{query}'")
                executor.memory["last_downloaded_image"] = result["path"]
                executor.memory["last_extracted"] = (
                    f'Downloaded image saved at: {result["path"]} '
                    f'({result["width"]}x{result["height"]})'
                )

            # 13. Attach previously downloaded image in active file picker
            elif intent == "attach_last_downloaded_image":
                image_path = executor.memory.get("last_downloaded_image")
                if not image_path:
                    raise Exception("No downloaded image in memory. Run download_image first.")
                
                logger.info(f"Loading actual image file into clipboard: {image_path}")
                # 🔥 FIX: Use PowerShell to copy the FILE OBJECT to the clipboard, not just the text path!
                import subprocess
                safe_path = image_path.replace("'", "''")
                subprocess.run(["powershell", "-command", f"Set-Clipboard -LiteralPath '{safe_path}'"])
                time.sleep(1.5) # Wait for Windows to process the heavy clipboard data
                
                pyautogui.hotkey("ctrl", "v")
                time.sleep(2.0) # Wait for WhatsApp to generate the image preview box
                
                # Press enter to confirm the attachment
                pyautogui.press("enter")
                time.sleep(FAST_ACTION_PAUSE_SECONDS)
                
            # 14. Run OS Terminal Command
            elif intent == "run_command":
                logger.info(f"Executing OS command: {val}")
                import subprocess
                try:
                    result = subprocess.run(val, shell=True, capture_output=True, text=True, timeout=15)
                    if result.stdout:
                        logger.info(f"Command Output: {result.stdout.strip()}")
                        executor.memory["last_extracted"] = result.stdout.strip()
                    if result.stderr:
                        logger.warning(f"Command Error: {result.stderr.strip()}")
                except Exception as e:
                    raise Exception(f"Failed to execute command '{val}': {e}")
                    
            # 15. Fallback for old strategies
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
            chain_success = False
            break
        except Exception as e:
            logger.error(f"Step {i+1} Failed: {e}")
            log_failure(task, str(e))
            if allow_recovery:
                logger.warning("Failure recorded. Attempting one adaptive recovery sub-plan...")
                current_screen = executor.screen.capture_full()
                recovery_goal = (
                    f"Recover from failed step. Failed intent='{intent}', target='{val}', error='{e}'. "
                    "Do not repeat the same failing method. Use an alternative approach."
                )
                recovery_tasks = planner.generate_sub_plan(recovery_goal, current_screen)
                if recovery_tasks:
                    logger.info("Adaptive recovery plan generated. Executing recovery steps...")
                    recovery_ok = run_task_chain(
                        recovery_tasks,
                        decision,
                        executor,
                        planner,
                        image_fetcher,
                        allow_recovery=False,
                    )
                    chain_success = chain_success and recovery_ok
                else:
                    logger.warning("Recovery planner could not generate tasks.")
                    chain_success = False
            else:
                logger.warning("Failure recorded in Learning Journal. Halting current chain.")
                chain_success = False
            break
        
    logger.info("=== Task Chain Complete ===")
    return chain_success

def ask_user_success_feedback():
    """Optional post-run feedback from user to improve learning signals."""
    try:
        answer = input("\nWas this result correct? [y/n/skip]: ").strip().lower()
    except Exception:
        return None
    if answer in {"y", "yes"}:
        return True
    if answer in {"n", "no"}:
        return False
    return None

def _is_message_query(user_prompt):
    text = str(user_prompt or "").lower()
    return any(token in text for token in ["message", "messages", "msg", "chat", "whatsapp", "sent"])

def _extract_contact_name(user_prompt):
    prompt = str(user_prompt or "").strip()
    patterns = [
        r"did\s+([a-zA-Z][a-zA-Z0-9 _.'-]{1,40})\s+send",
        r"from\s+([a-zA-Z][a-zA-Z0-9 _.'-]{1,40})",
        r"\bwith\s+([a-zA-Z][a-zA-Z0-9 _.'-]{1,40})\b",
    ]
    for pattern in patterns:
        m = re.search(pattern, prompt, flags=re.IGNORECASE)
        if m:
            name = m.group(1).strip(" .,!?:;\"'")
            if name:
                return name
    return None

def _resolve_contact_alias(name, user_preferences):
    if not name:
        return None
    contacts = (user_preferences or {}).get("contacts", {})
    if not isinstance(contacts, dict):
        return name
    mapped = contacts.get(name.lower())
    return mapped if mapped else name

def _format_result_output(user_prompt, extracted, user_preferences):
    style = (user_preferences or {}).get("default_result_style", "contact_quote")
    template = (user_preferences or {}).get("message_output_template", "{contact} said to you: \"{message}\"")
    text = str(extracted).strip()
    if not text:
        return None

    if _is_message_query(user_prompt) and style == "contact_quote":
        contact = _resolve_contact_alias(_extract_contact_name(user_prompt), user_preferences)
        if contact:
            try:
                return template.format(contact=contact, message=text)
            except Exception:
                return f'{contact} said to you: "{text}"'
        return f'Latest message says: "{text}"'
    return text

def finalize_run_feedback(agent_executor, user_prompt="", user_preferences=None):
    """Return focus to terminal and print useful extracted output."""
    try:
        agent_executor.os.focus_terminal_window()
    except Exception:
        pass

    extracted = agent_executor.memory.get("last_extracted")
    if extracted:
        formatted_output = _format_result_output(user_prompt, extracted, user_preferences or {})
        print("\n=== RESULT ===")
        print(formatted_output or extracted)
        print("==============")

def maybe_save_preference_from_prompt(user_prompt):
    """Detect and persist simple user preference statements."""
    prompt = user_prompt.strip()
    m = re.search(
        r"default messaging app is\s+([a-zA-Z0-9 _-]+)",
        prompt,
        flags=re.IGNORECASE,
    )
    if m:
        app_name = m.group(1).strip(" .,!?:;\"'")
        if app_name:
            set_user_preference("default_messaging_app", app_name)
            print(f"\nSaved preference: default messaging app = {app_name}")
            return True
    style_match = re.search(
        r"(default )?(result|output) (style|format) is\s+([a-zA-Z0-9 _-]+)",
        prompt,
        flags=re.IGNORECASE,
    )
    if style_match:
        style_name = style_match.group(4).strip(" .,!?:;\"'").lower().replace(" ", "_")
        allowed_styles = {"contact_quote", "plain"}
        if style_name not in allowed_styles:
            print(f"\nUnsupported result style '{style_name}'. Allowed: contact_quote, plain")
            return True
        set_user_preference("default_result_style", style_name)
        print(f"\nSaved preference: default result style = {style_name}")
        return True
    return False

if __name__ == "__main__":
    decision_engine, agent_executor, planner, observer, image_fetcher = initialize_agent()

    print("\n" + "="*50)
    print("Welcome to PCIA v0.2 - The Cognitive Agent")
    print("="*50)

    while True:
        system_context = observer.get_context()
        learning_history = get_recent_failure_summary(max_entries=20)
        print(f"\n[{system_context}]")

        user_prompt = input("\nWhat would you like me to do? \n> ").strip()
        if user_prompt.lower() in {"exit", "quit", "q"}:
            print("Goodbye.")
            break
        if not user_prompt:
            print("Please enter a task (or type 'exit').")
            continue
        
        # ── Personal Memory Commands ────────────────────────────────────────
        mem_cmd = parse_memory_command(user_prompt)
        if mem_cmd:
            action = mem_cmd["action"]
            if action == "remember":
                remember(mem_cmd["key"], mem_cmd["value"])
                print(f"\n🧠 Got it! I'll remember: [{mem_cmd['key']}] = {mem_cmd['value']}")
            elif action == "forget":
                removed = forget(mem_cmd["key"])
                if removed:
                    print(f"\n🧹 Done — I've forgotten: [{mem_cmd['key']}]")
                else:
                    print(f"\n❓ I don't have any memory called '{mem_cmd['key']}'.")
            elif action == "recall_all":
                memories = recall_all()
                if memories:
                    print("\n🧠 Here's everything I remember about you:")
                    for k, v in memories.items():
                        print(f"  • {k}: {v}")
                else:
                    print("\n🧠 I don't have any personal memories saved yet.")
            continue

        # Allow user to teach persistent preferences in natural language.
        if maybe_save_preference_from_prompt(user_prompt):
            continue

        # Real-time Learning / Teaching Mode
        prompt_low = user_prompt.lower()
        if "teach" in prompt_low or "learn" in prompt_low or "show you how" in prompt_low:
            # Extract skill name (e.g., "teach how to send a photo")
            skill_name = prompt_low.replace("teach me", "").replace("teach you", "").replace("teach", "").replace("how to", "").replace("i can", "").replace("i will", "").replace("i'll", "").replace("learn", "").replace("show you how", "").strip(" ?!")
            if not skill_name:
                print("Please provide a name for the skill. Example: 'teach how to copy an image'")
                continue
                
            from modules.skill_learner import SkillLearner
            learner = SkillLearner()
            print(f"\n[TEACHING MODE] I am ready to learn: '{skill_name}'")
            print("1. Press ENTER to start recording.")
            print("2. Perform the exact mouse clicks and keystrokes you want me to learn.")
            print("3. When finished, come back to this terminal and press ENTER to stop recording.")
            input("\nPress ENTER to start recording...")
            learner.start_recording()
            input("🔴 Recording... Press ENTER here when finished.")
            learner.stop_recording(skill_name)
            continue

        # Deterministic shortcut for a frequent request: avoid fragile visual scraping.
        if re.search(r"\b(open|running)\b.*\b(app|apps|windows)\b|\bwhat.?s open\b", user_prompt.lower()):
            logger.info("Using OS-level window enumeration shortcut for open-apps request.")
            open_windows = agent_executor.os.list_open_windows()
            if open_windows:
                print("\nOpen windows detected:")
                for name in open_windows:
                    print(f"- {name}")
                auto_success = True
            else:
                print("\nI couldn't enumerate open windows right now.")
                auto_success = False
            user_success = ask_user_success_feedback()
            log_run_history(
                user_prompt=user_prompt,
                method="os_window_enumeration",
                auto_success=auto_success,
                user_success=user_success,
                details=f"windows_count={len(open_windows)}"
            )
            continue

        logger.info("Generating Main Task Plan...")
        profile = load_user_profile()
        user_preferences = {
            "default_messaging_app": str(profile.get("default_messaging_app", "whatsapp")),
            "default_result_style": get_user_preference(
                "default_result_style",
                str(profile.get("default_result_style", "contact_quote")),
            ),
            "message_output_template": str(
                profile.get("message_output_template", "{contact} said to you: \"{message}\"")
            ),
            "contacts": profile.get("contacts", {}),
        }
        
        # Load full skill patterns for the planner to improvise with
        user_preferences["learned_skills_data"] = {}
        try:
            from modules.skill_learner import SkillLearner
            skills_dir = SkillLearner().skills_dir
            if skills_dir.exists():
                for f in skills_dir.glob("*.json"):
                    with open(f, "r") as json_file:
                        user_preferences["learned_skills_data"][f.stem] = json.load(json_file).get("semantic_plan", [])
        except Exception as e:
            logger.error(f"Failed to load skills data: {e}")
            
        # Inject personal memories into planner so the AI can use them
        personal_memory_summary = get_memory_summary()
        if personal_memory_summary:
            user_preferences["personal_memory"] = personal_memory_summary

        dynamic_chain = planner.generate_plan(
            user_prompt,
            system_context,
            learning_history,
            user_preferences=user_preferences,
        )

        if dynamic_chain:
            print("\n--- GENERATED PLAN ---")
            for step in dynamic_chain:
                print(f"- {step.get('intent')} -> {step.get('target_value')}")
            print("----------------------\n")
            
            logger.info("Starting execution in 3 seconds... hands off!")
            time.sleep(3)
            auto_success = run_task_chain(
                dynamic_chain,
                decision_engine,
                agent_executor,
                planner,
                image_fetcher,
            )
            finalize_run_feedback(agent_executor, user_prompt=user_prompt, user_preferences=user_preferences)
            user_success = ask_user_success_feedback()
            log_run_history(
                user_prompt=user_prompt,
                method="planner_chain",
                auto_success=auto_success,
                user_success=user_success,
                details=f"steps={len(dynamic_chain)}"
            )
        else:
            logger.error("Could not understand the request or API failed.")
            finalize_run_feedback(agent_executor, user_prompt=user_prompt, user_preferences=user_preferences)
            user_success = ask_user_success_feedback()
            log_run_history(
                user_prompt=user_prompt,
                method="planner_chain",
                auto_success=False,
                user_success=user_success,
                details="planner_failed_or_empty_chain"
            )