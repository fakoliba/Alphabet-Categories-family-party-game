"""Pure game rules for Alphabet Categories.

This module has no UI, file-system, or network dependencies so its rules can be
tested offline with Python's standard library.
"""

from __future__ import annotations

from datetime import datetime, timezone
import random
import uuid
from typing import Any

ALPHABET = tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
HARD_LETTERS = frozenset({"Q", "X", "Z"})
DEFAULT_CATEGORIES = ("Country", "Capital City", "Fruit", "Car Brand", "Animal")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_settings(settings: dict[str, Any]) -> dict[str, Any]:
    players = [
        {
            "id": str(player.get("id") or f"player-{index + 1}"),
            "name": str(player.get("name") or f"Player {index + 1}").strip(),
            "color": str(player.get("color") or "#f97316"),
        }
        for index, player in enumerate(settings.get("players", []))
    ]
    players = [player for player in players if player["name"]]
    categories = list(dict.fromkeys(
        str(category).strip()
        for category in settings.get("categories", DEFAULT_CATEGORIES)
        if str(category).strip()
    ))
    if not players:
        raise ValueError("Add at least one player to start.")
    if not categories:
        raise ValueError("Choose at least one category.")
    if len(players) > 8:
        raise ValueError("A game can have up to eight players.")

    timer_seconds = int(settings.get("timer_seconds", 60))
    if timer_seconds not in (0, 30, 60, 90):
        raise ValueError("Choose a 30, 60, 90 second, or no timer.")
    round_limit = settings.get("round_limit")
    round_limit = int(round_limit) if round_limit else None
    if round_limit is not None and round_limit < 1:
        raise ValueError("The round limit must be positive or off.")
    return {
        "players": players,
        "categories": categories,
        "timer_seconds": timer_seconds,
        "exclude_hard_letters": bool(settings.get("exclude_hard_letters", False)),
        "category_mode": "spin" if settings.get("category_mode") == "spin" else "sequence",
        "round_limit": round_limit,
        "sound_muted": bool(settings.get("sound_muted", False)),
    }


def new_game(settings: dict[str, Any], now: str | None = None) -> dict[str, Any]:
    normalized = normalize_settings(settings)
    return {
        "game_id": str(uuid.uuid4()),
        "status": "playing",
        "settings": normalized,
        "used_letters": [],
        "history": [],
        "scores": {player["id"]: 0 for player in normalized["players"]},
        "pending_turn": None,
        "created_at": now or _now_iso(),
        "completed_at": None,
    }


def eligible_letters(game: dict[str, Any]) -> list[str]:
    settings = game["settings"]
    return [
        letter
        for letter in ALPHABET
        if letter not in game["used_letters"]
        and not (settings["exclude_hard_letters"] and letter in HARD_LETTERS)
    ]


def should_finish(game: dict[str, Any]) -> bool:
    players_per_round = len(game["settings"]["players"])
    completed_rounds = len(game["history"]) // players_per_round
    round_limit = game["settings"]["round_limit"]
    return not eligible_letters(game) or (
        round_limit is not None and completed_rounds >= round_limit
    )


def _finish(game: dict[str, Any], now: str | None = None) -> None:
    game["status"] = "complete"
    game["completed_at"] = now or _now_iso()
    game["pending_turn"] = None


def draw_letter(
    game: dict[str, Any], rng: random.Random | None = None, now: float | None = None
) -> dict[str, Any] | None:
    if game["status"] != "playing" or game["pending_turn"] is not None:
        raise ValueError("Finish the current turn before drawing another letter.")
    if should_finish(game):
        _finish(game)
        return None

    chooser = rng or random.Random()
    available = eligible_letters(game)
    if not available:
        _finish(game)
        return None

    settings = game["settings"]
    turn_index = len(game["history"])
    player = settings["players"][turn_index % len(settings["players"])]
    if settings["category_mode"] == "spin":
        category = chooser.choice(settings["categories"])
    else:
        category = settings["categories"][turn_index % len(settings["categories"])]
    letter = chooser.choice(available)
    game["used_letters"].append(letter)
    game["pending_turn"] = {
        "turn_number": turn_index + 1,
        "round_number": turn_index // len(settings["players"]) + 1,
        "player_id": player["id"],
        "letter": letter,
        "category": category,
        "started_at": now if now is not None else datetime.now(timezone.utc).timestamp(),
        "answer_draft": "",
    }
    return game["pending_turn"]


def submit_answer(
    game: dict[str, Any], answer: str, accepted: bool, now: str | None = None
) -> dict[str, Any]:
    pending = game.get("pending_turn")
    if game["status"] != "playing" or pending is None:
        raise ValueError("There is no answer waiting to be recorded.")
    player = next(
        player for player in game["settings"]["players"]
        if player["id"] == pending["player_id"]
    )
    record = {
        **pending,
        "player_name": player["name"],
        "answer": str(answer or "").strip(),
        "accepted": bool(accepted),
        "points": 1 if accepted else 0,
        "completed_at": now or _now_iso(),
    }
    game["history"].append(record)
    if record["accepted"]:
        game["scores"][record["player_id"]] += 1
    game["pending_turn"] = None
    if should_finish(game):
        _finish(game, now)
    return record


def scoreboard(game: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(
        [
            {**player, "score": game["scores"].get(player["id"], 0)}
            for player in game["settings"]["players"]
        ],
        key=lambda player: (-player["score"], player["name"].casefold()),
    )


def winners(game: dict[str, Any]) -> list[dict[str, Any]]:
    board = scoreboard(game)
    highest = board[0]["score"]
    return [player for player in board if player["score"] == highest]
