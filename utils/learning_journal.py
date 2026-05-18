import json
import os
from datetime import datetime
from utils.logger import get_logger

logger = get_logger("LearningJournal")
JOURNAL_PATH = "data/learning_log.json"
HISTORY_PATH = "data/run_history.json"
PREFERENCES_PATH = "data/user_preferences.json"

def _ensure_data_dir():
    if not os.path.exists("data"):
        os.makedirs("data")

def _read_json_list(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []

def log_failure(task, reason):
    _ensure_data_dir()
    data = _read_json_list(JOURNAL_PATH)
    
    data.append({"failed_task": task, "reason": reason})
    
    with open(JOURNAL_PATH, "w") as f:
        json.dump(data, f, indent=4)
    logger.info("Failure logged to memory. I will learn from this.")

def log_run_history(user_prompt, method, auto_success, user_success=None, details=None):
    """
    Stores every run (success/failure) for better learning signals.
    user_success can be: True, False, or None (skip/unknown).
    """
    _ensure_data_dir()
    history = _read_json_list(HISTORY_PATH)
    history.append({
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "user_prompt": user_prompt,
        "method": method,
        "auto_success": bool(auto_success),
        "user_success": user_success,
        "details": details or ""
    })
    with open(HISTORY_PATH, "w") as f:
        json.dump(history, f, indent=4)
    logger.info("Run history entry recorded.")

def get_learning_history():
    if not os.path.exists(JOURNAL_PATH): 
        return "No past mistakes."
    with open(JOURNAL_PATH, "r") as f:
        return f.read()

def get_recent_failure_summary(max_entries=20):
    """Return a compact, planner-friendly summary of recent failures."""
    if not os.path.exists(JOURNAL_PATH):
        return "No past mistakes."

    try:
        with open(JOURNAL_PATH, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return "No past mistakes."

    if not isinstance(data, list) or not data:
        return "No past mistakes."

    recent = data[-max_entries:]
    lines = []
    for item in recent:
        task = item.get("failed_task", {}) if isinstance(item, dict) else {}
        reason = item.get("reason", "unknown failure") if isinstance(item, dict) else "unknown failure"
        intent = task.get("intent", "unknown_intent") if isinstance(task, dict) else "unknown_intent"
        target = task.get("target_value", "") if isinstance(task, dict) else ""
        lines.append(f"- intent={intent}; target={target}; reason={reason}")

    return "\n".join(lines) if lines else "No past mistakes."

def _read_json_object(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}

def set_user_preference(key, value):
    """Persist a user preference across runs."""
    _ensure_data_dir()
    prefs = _read_json_object(PREFERENCES_PATH)
    prefs[str(key)] = value
    with open(PREFERENCES_PATH, "w") as f:
        json.dump(prefs, f, indent=4)
    logger.info(f"Preference saved: {key}={value}")

def get_user_preference(key, default=None):
    prefs = _read_json_object(PREFERENCES_PATH)
    return prefs.get(key, default)