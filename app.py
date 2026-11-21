"""Streamlit UI for the fully local Alphabet Categories game."""

from __future__ import annotations

from datetime import datetime, timezone
import html
import time

import streamlit as st

from alphabet_categories import game as rules
from alphabet_categories.storage import load_data, save_data


st.set_page_config(page_title="Alphabet Categories", page_icon="🔤", layout="wide")

PALETTE = {
    "Tangerine": "#f97316",
    "Ocean": "#2563eb",
    "Teal": "#0f9b8e",
    "Berry": "#d9468f",
    "Violet": "#8b5cf6",
    "Sunshine": "#ca8a04",
    "Mint": "#16a085",
    "Cherry": "#ef4444",
}
COLOR_NAME = {value: name for name, value in PALETTE.items()}
DEFAULT_SETTINGS = {
    "players": [
        {"id": "player-1", "name": "Player 1", "color": PALETTE["Tangerine"]},
        {"id": "player-2", "name": "Player 2", "color": PALETTE["Ocean"]},
    ],
    "categories": list(rules.DEFAULT_CATEGORIES),
    "timer_seconds": 60,
    "exclude_hard_letters": False,
    "category_mode": "sequence",
    "round_limit": None,
    "sound_muted": False,
}

st.markdown(
    """
    <style>
    .stApp { background: #fff8e8; color: #263343; }
    .block-container { max-width: 1120px; padding-top: 1.5rem; }
    h1, h2, h3 { color: #263343; }
    .hero { text-align: center; padding: .8rem 0 1rem; }
    .eyebrow { color: #f97316; font-weight: 900; letter-spacing: .12em; text-transform: uppercase; font-size: .78rem; }
    .subtitle { color: #677487; }
    .letter-tile { display: grid; place-items: center; border-radius: 12px; margin: 3px 0 9px;
      min-height: 48px; color: #573e0d; background: #f5c84b; box-shadow: 0 4px 0 #d6a937;
      font-size: 1.35rem; font-weight: 1000; }
    .letter-tile.used { background: #e7e8ea; color: #9ba0a7; box-shadow: 0 3px 0 #c9cbd0; }
    .letter-tile.excluded { background: #f1eadb; color: #c5bda9; box-shadow: 0 3px 0 #ded5c2; }
    .big-letter { display: grid; place-items: center; min-height: 210px; border-radius: 22px;
      background: #fff0ca; color: #bd6712; font-size: clamp(5rem, 18vw, 10rem); font-weight: 1000;
      text-shadow: 0 6px 0 #f0c05a; }
    .category-card { border-radius: 16px; padding: 16px; margin: 12px 0; background: #fff2d1; text-align: center; }
    .winner-card { border-radius: 18px; padding: 22px; background: #fff0ca; text-align: center; }
    .winner-name { color: #b95c0c; font-size: clamp(1.7rem, 5vw, 2.8rem); font-weight: 1000; }
    div[data-testid="stAudio"] { height: 0; overflow: hidden; margin: 0; padding: 0; }
    @media (max-width: 640px) { .block-container { padding: 1rem .8rem; } }
    </style>
    """,
    unsafe_allow_html=True,
)


if "local_data" not in st.session_state:
    st.session_state.local_data = load_data()
if "settings" not in st.session_state:
    st.session_state.settings = st.session_state.local_data.get("settings") or DEFAULT_SETTINGS
if "game" not in st.session_state:
    st.session_state.game = st.session_state.local_data.get("active_game")
if "player_rows" not in st.session_state:
    st.session_state.player_rows = [dict(player) for player in st.session_state.settings["players"]]
if "categories" not in st.session_state:
    st.session_state.categories = list(st.session_state.settings["categories"])
if "sound_event" not in st.session_state:
    st.session_state.sound_event = None


def save_current_state() -> None:
    st.session_state.local_data["settings"] = st.session_state.settings
    st.session_state.local_data["active_game"] = st.session_state.game
    try:
        save_data(st.session_state.local_data)
        st.session_state.save_error = ""
    except OSError:
        st.session_state.save_error = "Could not save to this device. Check the folder permissions."


def queue_sound(frequency: int) -> None:
    if not st.session_state.settings.get("sound_muted", False):
        st.session_state.sound_event = frequency


def render_queued_sound() -> None:
    frequency = st.session_state.sound_event
    if frequency is None:
        return
    import io
    import math
    import struct
    import wave

    sample_rate = 22050
    duration = 0.12
    samples = int(sample_rate * duration)
    frames = bytearray()
    for sample in range(samples):
        envelope = 1 - sample / samples
        value = int(7000 * envelope * math.sin(2 * math.pi * frequency * sample / sample_rate))
        frames.extend(struct.pack("<h", value))
    output = io.BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(frames)
    st.audio(output.getvalue(), format="audio/wav", autoplay=True, width=1)
    st.session_state.sound_event = None


def archive_if_complete() -> None:
    game = st.session_state.game
    if not game or game["status"] != "complete":
        return
    past_games = st.session_state.local_data.setdefault("past_games", [])
    if not any(past.get("game_id") == game["game_id"] for past in past_games):
        past_games.insert(0, game)
        del past_games[25:]


def read_player_rows() -> list[dict[str, str]]:
    players = []
    for index, _row in enumerate(st.session_state.player_rows):
        players.append({
            "id": f"player-{index + 1}",
            "name": st.session_state.get(f"player_name_{index}", "").strip(),
            "color": PALETTE[st.session_state.get(f"player_color_{index}", "Tangerine")],
        })
    return players


def remove_player(index: int) -> None:
    rows = read_player_rows()
    rows.pop(index)
    for position, player in enumerate(rows):
        st.session_state[f"player_name_{position}"] = player["name"]
        st.session_state[f"player_color_{position}"] = COLOR_NAME.get(player["color"], "Tangerine")
    st.session_state.player_rows = rows


def add_player() -> None:
    rows = read_player_rows()
    rows.append({"id": f"player-{len(rows) + 1}", "name": f"Player {len(rows) + 1}", "color": list(PALETTE.values())[len(rows) % len(PALETTE)]})
    st.session_state.player_rows = rows


def remove_category(index: int) -> None:
    st.session_state.categories.pop(index)


def update_game_mute() -> None:
    game = st.session_state.game
    if game:
        game["settings"]["sound_muted"] = st.session_state.game_mute
        st.session_state.settings["sound_muted"] = st.session_state.game_mute
        save_current_state()


def show_setup() -> None:
    st.markdown('<div class="hero"><div class="eyebrow">A family word game</div><h1>Pick a letter. Name your answer!</h1><p class="subtitle">Take turns, think fast, and see who can name the most things before the alphabet runs out.</p></div>', unsafe_allow_html=True)
    players_col, rules_col = st.columns([1.2, 0.8], gap="large")

    with players_col:
        st.subheader("Who's playing?")
        for index, player in enumerate(st.session_state.player_rows):
            name_col, color_col, remove_col = st.columns([5, 2, 1])
            with name_col:
                st.text_input("Player name", value=player["name"], key=f"player_name_{index}", max_chars=28, label_visibility="collapsed", placeholder=f"Player {index + 1}")
            current_color = COLOR_NAME.get(player["color"], "Tangerine")
            with color_col:
                st.selectbox("Player color", list(PALETTE), index=list(PALETTE).index(current_color), key=f"player_color_{index}", label_visibility="collapsed")
            with remove_col:
                st.button("×", key=f"remove_player_{index}", help="Remove player", disabled=len(st.session_state.player_rows) <= 1, on_click=remove_player, args=(index,))

        st.button("＋ Add player", disabled=len(st.session_state.player_rows) >= 8, on_click=add_player)

        st.subheader("Categories")
        category_columns = st.columns(min(3, max(1, len(st.session_state.categories))))
        for index, category in enumerate(list(st.session_state.categories)):
            with category_columns[index % len(category_columns)]:
                st.button(f"{category}  ×", key=f"remove_category_{index}", help="Remove category", on_click=remove_category, args=(index,))
        with st.form("add_category_form", clear_on_submit=True):
            new_category = st.text_input("Add your own category", max_chars=32, placeholder="For example: Favorite food")
            add_category = st.form_submit_button("Add category")
        if add_category:
            value = new_category.strip()
            if value and value.casefold() not in {item.casefold() for item in st.session_state.categories}:
                st.session_state.categories.append(value)
                st.rerun()
            elif value:
                st.warning("That category is already on the list.")

    with rules_col:
        st.subheader("Round settings")
        timer_label = st.selectbox("Timer", ["30 seconds", "60 seconds", "90 seconds", "Off"], index={30: 0, 60: 1, 90: 2, 0: 3}.get(st.session_state.settings["timer_seconds"], 1), key="timer_choice")
        category_mode = st.selectbox("Category order", ["In order", "Spin randomly"], index=1 if st.session_state.settings["category_mode"] == "spin" else 0, key="category_mode_choice")
        round_label = st.selectbox("Game length", ["Until letters run out", "3 rounds", "5 rounds", "10 rounds"], index={None: 0, 3: 1, 5: 2, 10: 3}.get(st.session_state.settings["round_limit"], 0), key="round_choice")
        exclude_hard = st.checkbox("Skip tricky letters Q, X, and Z", value=st.session_state.settings["exclude_hard_letters"], key="exclude_hard_choice")
        sound_muted = st.checkbox("Mute sound effects", value=st.session_state.settings.get("sound_muted", False), key="sound_muted_choice")
        st.caption("Players, answers, and past games stay in a save file on this device. No account or internet connection is needed.")

    if st.session_state.get("save_error"):
        st.warning(st.session_state.save_error)

    if st.button("Start the game →", type="primary", use_container_width=True):
        players = read_player_rows()
        if any(not player["name"] for player in players):
            st.error("Give every player a name.")
            return
        if not st.session_state.categories:
            st.error("Choose at least one category.")
            return
        timer_seconds = {"30 seconds": 30, "60 seconds": 60, "90 seconds": 90, "Off": 0}[timer_label]
        round_limit = {"Until letters run out": None, "3 rounds": 3, "5 rounds": 5, "10 rounds": 10}[round_label]
        settings = {
            "players": players,
            "categories": list(st.session_state.categories),
            "timer_seconds": timer_seconds,
            "exclude_hard_letters": exclude_hard,
            "category_mode": "spin" if category_mode == "Spin randomly" else "sequence",
            "round_limit": round_limit,
            "sound_muted": sound_muted,
        }
        try:
            st.session_state.settings = rules.normalize_settings(settings)
            st.session_state.game = rules.new_game(st.session_state.settings)
            st.session_state.local_data["settings"] = st.session_state.settings
            save_current_state()
            st.rerun()
        except ValueError as error:
            st.error(str(error))

    past_games = st.session_state.local_data.get("past_games", [])
    if past_games:
        st.divider()
        st.subheader("Recent games")
        for past in past_games[:5]:
            name_list = " & ".join(player["name"] for player in rules.winners(past))
            st.caption(f"🏆 {name_list} · {len(past['history'])} turns · {len(past['used_letters'])} letters")


def remaining_seconds(game: dict) -> int | None:
    turn = game.get("pending_turn")
    timer = game["settings"]["timer_seconds"]
    if not turn or not timer:
        return None
    elapsed = time.time() - float(turn["started_at"])
    return max(0, int(timer - elapsed + 0.999))


@st.fragment(run_every="1s")
def show_timer(game_id: str) -> None:
    game = st.session_state.game
    turn = game.get("pending_turn") if game and game.get("game_id") == game_id else None
    if not turn:
        return
    left = remaining_seconds(game)
    if left is None:
        st.caption("Timer is off")
    elif left == 0:
        st.error("Time is up! Finish the family vote.")
    else:
        st.metric("Time left", f"{left}s")


def render_letter_board(game: dict) -> None:
    st.markdown("### Letter board")
    columns = st.columns(7)
    used = set(game["used_letters"])
    for index, letter in enumerate(rules.ALPHABET):
        excluded = game["settings"]["exclude_hard_letters"] and letter in rules.HARD_LETTERS
        classes = ["letter-tile"]
        if letter in used:
            classes.append("used")
        if excluded:
            classes.append("excluded")
        with columns[index % len(columns)]:
            st.markdown(f'<div class="{" ".join(classes)}">{letter}</div>', unsafe_allow_html=True)


def show_game() -> None:
    game = st.session_state.game
    archive_if_complete()
    save_current_state()
    st.sidebar.checkbox(
        "Mute sound effects",
        value=game["settings"].get("sound_muted", False),
        key="game_mute",
        on_change=update_game_mute,
    )
    st.sidebar.caption("Game data is saved on this device only.")
    header_col, action_col = st.columns([4, 1])
    with header_col:
        st.markdown('<div class="eyebrow">Pass & play</div>', unsafe_allow_html=True)
        st.title("Alphabet Categories")
    with action_col:
        if st.button("Change setup"):
            if game["status"] == "complete":
                st.session_state.game = None
                save_current_state()
                st.rerun()
            else:
                st.session_state.confirm_change = True
    if st.session_state.get("confirm_change"):
        st.warning("Leave this game? The unfinished game will not appear in past games.")
        discard_col, keep_col = st.columns(2)
        with discard_col:
            if st.button("Leave game", type="primary"):
                st.session_state.game = None
                st.session_state.confirm_change = False
                save_current_state()
                st.rerun()
        with keep_col:
            if st.button("Keep playing"):
                st.session_state.confirm_change = False
                st.rerun()

    if game["status"] == "complete":
        winning_players = rules.winners(game)
        names = " & ".join(player["name"] for player in winning_players)
        lead = "It's a tie!" if len(winning_players) > 1 else "We have a winner!"
        score = winning_players[0]["score"]
        st.markdown(f'<div class="winner-card"><div class="eyebrow">{lead}</div><div class="winner-name">🏆 {html.escape(names)}</div><p>Final score: {score} · {len(game["history"])} turns played</p></div>', unsafe_allow_html=True)
        if st.session_state.get("celebrated_game") != game["game_id"]:
            st.balloons()
            st.session_state.celebrated_game = game["game_id"]
        if st.button("Play again with the same setup", type="primary"):
            st.session_state.game = rules.new_game(st.session_state.settings)
            save_current_state()
            st.rerun()

    render_letter_board(game)
    left_col, right_col = st.columns([1.5, 1], gap="large")
    with left_col:
        if game["status"] == "playing" and game["pending_turn"] is None:
            turn_index = len(game["history"])
            player = game["settings"]["players"][turn_index % len(game["settings"]["players"])]
            round_number = turn_index // len(game["settings"]["players"]) + 1
            left = len(rules.eligible_letters(game))
            st.info(f"Round {round_number} · {player['name']}'s turn · {left} letters left")
            if st.button("🎲 Draw a letter", type="primary", use_container_width=True):
                turn = rules.draw_letter(game)
                if turn is None:
                    archive_if_complete()
                else:
                    queue_sound(570)
                save_current_state()
                st.rerun()
        elif game["status"] == "playing":
            turn = game["pending_turn"]
            player = next(person for person in game["settings"]["players"] if person["id"] == turn["player_id"])
            st.markdown(f'<div class="big-letter">{turn["letter"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="category-card"><div class="eyebrow">{html.escape(player["name"])} · round {turn["round_number"]}</div><h2>Name a {html.escape(turn["category"].lower())}</h2></div>', unsafe_allow_html=True)
            show_timer(game["game_id"])
            answer_key = f"answer_{game['game_id']}_{turn['turn_number']}"
            answer = st.text_input("Answer (optional record)", value=turn.get("answer_draft", ""), key=answer_key, placeholder="Type it here or say it out loud")
            turn["answer_draft"] = answer
            accept_col, reject_col = st.columns(2)
            with accept_col:
                accepted = st.button("👍 Accept · +1", type="primary", use_container_width=True)
            with reject_col:
                rejected = st.button("👎 Reject · 0", use_container_width=True)
            if accepted or rejected:
                rules.submit_answer(game, answer, accepted=accepted)
                archive_if_complete()
                queue_sound(760 if accepted else 240)
                save_current_state()
                st.rerun()
        else:
            st.success("Great game! The alphabet is complete.")

    with right_col:
        st.subheader("Scoreboard")
        for player in rules.scoreboard(game):
            st.markdown(f'<div style="padding:9px 12px;margin:6px 0;border:1px solid #ecdfc4;border-radius:12px;background:#fffdf7"><span style="color:{player["color"]}">●</span> <b>{html.escape(player["name"])}</b><span style="float:right;font-size:1.2rem;font-weight:900">{player["score"]}</span></div>', unsafe_allow_html=True)

    st.divider()
    st.subheader("Round history")
    if not game["history"]:
        st.caption("Completed turns will appear here.")
    else:
        for turn in reversed(game["history"]):
            answer_text = f" · “{turn['answer']}”" if turn.get("answer") else ""
            point_text = "+1 point" if turn["accepted"] else "no point"
            st.caption(f"Round {turn['round_number']} · {turn['player_name']} · {turn['letter']} / {turn['category']}{answer_text} · {point_text}")


if st.session_state.game:
    archive_if_complete()
    render_queued_sound()
    show_game()
else:
    show_setup()
    render_queued_sound()
