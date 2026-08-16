import json
import os
from threading import Lock

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(DATA_DIR, exist_ok=True)

_lock = Lock()


def _path(filename: str) -> str:
    return os.path.join(DATA_DIR, filename)


def load(filename: str, default=None):
    """Load a JSON file from the data folder. Returns `default` if it doesn't exist."""
    path = _path(filename)
    if not os.path.exists(path):
        return default if default is not None else {}
    with _lock:
        with open(path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return default if default is not None else {}


def save(filename: str, data):
    """Save data as JSON into the data folder."""
    path = _path(filename)
    with _lock:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
