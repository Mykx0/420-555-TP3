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


def get(pin):
    with _lock:
        return _load().get(pin)


def put(pin, name, passcode):
    with _lock:
        data = _load()
        if pin in data:
            return False
        data[pin] = {"name" : name, "passcode": passcode}
        _save(data)
        return True
    
def set_passcode(pin, new_passcode):
    with _lock:
        data = _load()
        if pin not in data:
            return False
        data[pin]["passcode"] = new_passcode
        _save(data)
        return True