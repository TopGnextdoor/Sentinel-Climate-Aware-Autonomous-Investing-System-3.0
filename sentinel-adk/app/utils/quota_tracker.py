import os
import json
from datetime import datetime

QUOTA_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "quota_log.json")
FLASH_LIMIT = 250
FLASH_LITE_LIMIT = 1000

def _load_data() -> dict:
    os.makedirs(os.path.dirname(QUOTA_FILE), exist_ok=True)
    if not os.path.exists(QUOTA_FILE):
        return {
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "flash_calls": 0,
            "flash_lite_calls": 0
        }
    try:
        with open(QUOTA_FILE, "r") as f:
            data = json.load(f)
        
        # Check for date reset
        today = datetime.utcnow().strftime("%Y-%m-%d")
        if data.get("date") != today:
            data = {
                "date": today,
                "flash_calls": 0,
                "flash_lite_calls": 0
            }
            _save_data(data)
        return data
    except Exception:
        return {
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "flash_calls": 0,
            "flash_lite_calls": 0
        }

def _save_data(data: dict):
    os.makedirs(os.path.dirname(QUOTA_FILE), exist_ok=True)
    try:
        with open(QUOTA_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def track_call(model_name: str):
    data = _load_data()
    # Normalize model name
    model_name = str(model_name).lower()
    if "flash-lite" in model_name:
        data["flash_lite_calls"] += 1
    elif "flash" in model_name:
        data["flash_calls"] += 1
    else:
        # Default fallback
        data["flash_lite_calls"] += 1
    _save_data(data)

def get_quota_summary() -> dict:
    data = _load_data()
    flash_calls = data.get("flash_calls", 0)
    flash_lite_calls = data.get("flash_lite_calls", 0)
    
    flash_remaining = max(0, FLASH_LIMIT - flash_calls)
    flash_lite_remaining = max(0, FLASH_LITE_LIMIT - flash_lite_calls)
    
    warning = None
    if flash_remaining < 50:
        warning = "Flash quota below 50"
    elif flash_lite_remaining < 200:
        warning = "Flash Lite quota below 200"
        
    return {
        "flash_calls_today": flash_calls,
        "flash_lite_calls_today": flash_lite_calls,
        "flash_remaining_approx": flash_remaining,
        "flash_lite_remaining_approx": flash_lite_remaining,
        "warning": warning
    }
