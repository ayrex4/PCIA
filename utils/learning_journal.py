import json
import os
from utils.logger import get_logger

logger = get_logger("LearningJournal")
JOURNAL_PATH = "data/learning_log.json"

def log_failure(task, reason):
    if not os.path.exists("data"): 
        os.makedirs("data")
    
    data =[]
    if os.path.exists(JOURNAL_PATH):
        with open(JOURNAL_PATH, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data =[]
    
    data.append({"failed_task": task, "reason": reason})
    
    with open(JOURNAL_PATH, "w") as f:
        json.dump(data, f, indent=4)
    logger.info("Failure logged to memory. I will learn from this.")

def get_learning_history():
    if not os.path.exists(JOURNAL_PATH): 
        return "No past mistakes."
    with open(JOURNAL_PATH, "r") as f:
        return f.read()