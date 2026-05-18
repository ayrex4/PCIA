"""
memory_store.py
---------------
Persistent, personal memory for PCIA.

Two distinct layers:
  - data/memory.json  : Arbitrary personal facts the user explicitly asks to remember.
                        (e.g. "my car is a Golf 7", "I prefer dark themes")
  - data/user_profile.json : Structured preferences already handled elsewhere.

API:
  remember(key, value)   -> saves a fact
  recall(key)            -> retrieves one fact (None if unknown)
  recall_all()           -> returns the full dict of memories
  forget(key)            -> removes a fact
  get_memory_summary()   -> compact string for injecting into planner prompts
"""

import json
import os
import re
from datetime import datetime
from utils.logger import get_logger

logger = get_logger("MemoryStore")

MEMORY_PATH = "data/memory.json"


# ─────────────────────────────────────────────
#  Internal helpers
# ─────────────────────────────────────────────

def _ensure_data_dir():
    os.makedirs("data", exist_ok=True)


def _read() -> dict:
    if not os.path.exists(MEMORY_PATH):
        return {}
    try:
        with open(MEMORY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _write(data: dict):
    _ensure_data_dir()
    with open(MEMORY_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ─────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────

def remember(key: str, value: str) -> None:
    """Persist a personal fact."""
    key = key.strip().lower()
    data = _read()
    data[key] = {
        "value": str(value).strip(),
        "saved_at": datetime.now().isoformat(timespec="seconds"),
    }
    _write(data)
    logger.info(f"Memory saved: [{key}] = {value}")


def recall(key: str):
    """Return the value for a key, or None."""
    data = _read()
    entry = data.get(key.strip().lower())
    if entry and isinstance(entry, dict):
        return entry.get("value")
    return None


def recall_all() -> dict:
    """Return all memories as {key: value} (without metadata)."""
    data = _read()
    return {k: v["value"] for k, v in data.items() if isinstance(v, dict) and "value" in v}


def forget(key: str) -> bool:
    """Remove a specific memory. Returns True if it existed."""
    data = _read()
    key = key.strip().lower()
    if key in data:
        del data[key]
        _write(data)
        logger.info(f"Memory forgotten: [{key}]")
        return True
    return False


def get_memory_summary() -> str:
    """
    Returns a compact, planner-friendly string like:
      'my car: Golf 7 | preferred theme: dark | sister: Houda'
    Returns empty string if no memories saved.
    """
    memories = recall_all()
    if not memories:
        return ""
    parts = [f"{k}: {v}" for k, v in memories.items()]
    return " | ".join(parts)


# ─────────────────────────────────────────────
#  Natural-language command parser
# ─────────────────────────────────────────────

# Patterns that signal "save this fact"
_REMEMBER_PATTERNS = [
    # "remember that my car is a Golf 7"
    r"remember\s+(?:that\s+)?(?:my\s+)?(.+?)\s+is\s+(.+)",
    # "remember I prefer dark mode"
    r"remember\s+(?:that\s+)?i\s+prefer\s+(.+)",
    # "remember this: key = value"
    r"remember\s+(?:this\s*[:\-])?\s*(.+?)\s*[=:]\s*(.+)",
    # "note that my timezone is Africa/Casablanca"
    r"note\s+(?:that\s+)?(?:my\s+)?(.+?)\s+is\s+(.+)",
    # "save that my name is Ayman"
    r"save\s+(?:that\s+)?(?:my\s+)?(.+?)\s+is\s+(.+)",
    # "store this: dark_mode = true"
    r"store\s+(?:this\s*[:\-])?\s*(.+?)\s*[=:]\s*(.+)",
]

# Patterns that signal "forget this fact"
_FORGET_PATTERNS = [
    r"forget\s+(?:about\s+)?(?:my\s+)?(.+)",
    r"delete\s+(?:memory\s+)?(?:about\s+)?(?:my\s+)?(.+)",
    r"remove\s+(?:memory\s+)?(?:about\s+)?(?:my\s+)?(.+)",
]

# Patterns that signal "what do you remember"
_RECALL_PATTERNS = [
    r"what\s+do\s+you\s+(?:know|remember)",
    r"show\s+(?:me\s+)?(?:my\s+)?memories",
    r"list\s+(?:my\s+)?memories",
    r"what\s+did\s+i\s+tell\s+you",
    r"recall\s+(?:everything|all)",
    r"memory\s+(?:list|dump|show)",
]


def parse_memory_command(user_prompt: str):
    """
    Detect if the user prompt is a memory command. Returns a dict:
      {"action": "remember", "key": ..., "value": ...}
      {"action": "forget",   "key": ...}
      {"action": "recall_all"}
      None   <- not a memory command
    """
    text = user_prompt.strip()
    lower = text.lower()

    # ── Check for recall-all command ──
    for pat in _RECALL_PATTERNS:
        if re.search(pat, lower):
            return {"action": "recall_all"}

    # ── Check for forget command ──
    for pat in _FORGET_PATTERNS:
        m = re.search(pat, lower)
        if m:
            key = m.group(1).strip(" .,!?:;\"'")
            return {"action": "forget", "key": key}

    # ── Check for remember command ──
    # Pattern 1: "remember that my X is Y" or "remember my X is Y"
    m = re.search(r"remember\s+(?:that\s+)?my\s+(.+?)\s+is\s+(.+)", lower)
    if m:
        return {"action": "remember", "key": m.group(1).strip(), "value": m.group(2).strip(" .,!?:;\"'")}

    # Pattern 2: "remember that X is Y"
    m = re.search(r"remember\s+(?:that\s+)?(.+?)\s+is\s+(.+)", lower)
    if m:
        return {"action": "remember", "key": m.group(1).strip(), "value": m.group(2).strip(" .,!?:;\"'")}

    # Pattern 3: "remember I prefer X"  (key becomes "preference", value = X)
    m = re.search(r"remember\s+(?:that\s+)?i\s+prefer\s+(.+)", lower)
    if m:
        return {"action": "remember", "key": "preference", "value": m.group(1).strip(" .,!?:;\"'")}

    # Pattern 4: "remember key=value" or "remember key: value"
    m = re.search(r"remember\s+(.+?)\s*[=:]\s*(.+)", lower)
    if m:
        return {"action": "remember", "key": m.group(1).strip(), "value": m.group(2).strip(" .,!?:;\"'")}

    # Pattern 5: "note/save/store that my X is Y"
    m = re.search(r"(?:note|save|store)\s+(?:that\s+)?(?:my\s+)?(.+?)\s+is\s+(.+)", lower)
    if m:
        return {"action": "remember", "key": m.group(1).strip(), "value": m.group(2).strip(" .,!?:;\"'")}

    return None
