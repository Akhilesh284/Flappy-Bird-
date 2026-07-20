"""
Small helper around a single JSON save file (save_data.json) that stores
everything except the legacy high score (which stays in highscore.txt for
backwards compatibility with the original game).
"""
import json
import os

from constants import ACHIEVEMENTS, SKIN_ORDER

SAVE_PATH = "save_data.json"

DEFAULT_DATA = {
    "volume": 0.7,
    "night_mode": False,
    "selected_skin": "red",
    "unlocked_skins": ["red"],
    "achievements": {aid: False for aid in ACHIEVEMENTS},
    "best_medal": None,
}


def load_data():
    if not os.path.exists(SAVE_PATH):
        return DEFAULT_DATA.copy()
    try:
        with open(SAVE_PATH, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return DEFAULT_DATA.copy()

    # merge with defaults so new fields added in future updates don't crash
    # on an older save file
    merged = DEFAULT_DATA.copy()
    merged.update(data)
    merged["achievements"] = {**DEFAULT_DATA["achievements"], **data.get("achievements", {})}
    if not merged.get("unlocked_skins"):
        merged["unlocked_skins"] = ["red"]
    return merged


def save_data(data):
    try:
        with open(SAVE_PATH, "w") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass
