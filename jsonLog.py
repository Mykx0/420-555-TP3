import json
import os
import threading
from datetime import datetime

FILE = os.path.join(os.path.dirname(__file__), "activity.json")
_lock = threading.Lock()


def _load():
    if not os.path.exists(FILE):
        return {}
    with open(FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _save(data):
    tmp = FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, FILE)


def log(level, action, message):
    with _lock:
        data = _load()
        key = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        data[key] = {"level": level.upper(), "action": action, "message": message}
        _save(data)


def info(action, message):    log("INFO", action, message)
def warning(action, message): log("WARNING", action, message)
def error(action, message):   log("ERROR", action, message)