"""Device-local JSON persistence. No account or network storage is used."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

APP_DIR = Path.home() / ".alphabet-categories"
SAVE_FILE = APP_DIR / "save.json"


def load_data(path: Path = SAVE_FILE) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("Save data must be an object")
        return {
            "settings": value.get("settings"),
            "active_game": value.get("active_game"),
            "past_games": value.get("past_games", []) if isinstance(value.get("past_games", []), list) else [],
        }
    except (OSError, ValueError, json.JSONDecodeError):
        return {"settings": None, "active_game": None, "past_games": []}


def save_data(data: dict[str, Any], path: Path = SAVE_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)
