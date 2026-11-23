import json
import os
import threading

FILE = os.path.join(os.path.dirname(__file__), "users.json")
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
        json.dump(data, f, indent=2)
    os.replace(tmp, FILE)  # atomic: avoids a corrupted file if the app crashes mid-write


def get(email):
    with _lock:
        return _load().get(email)


def put(email, password):
    with _lock:
        data = _load()
        if email in data:
            return False
        data[email] = password
        _save(data)
        return True