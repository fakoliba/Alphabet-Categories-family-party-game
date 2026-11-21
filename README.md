# Alphabet Categories

An offline-first family party game. Pick a letter, name something in a category, and let everyone at the table vote.

## Run it

The app is written in Python and uses Streamlit for its local interface. It does not use OpenAI, online job feeds, accounts, analytics, remote fonts, or remote assets. Install the one UI dependency before an offline session:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Start the app on the same computer:

```sh
streamlit run app.py --server.address 127.0.0.1
```

Streamlit opens the game in a browser through the computer's local loopback connection. The app binds only to `127.0.0.1`, and Streamlit usage statistics are disabled in `.streamlit/config.toml`. Gameplay and saving do not require internet access. Game settings, player names, and past results are stored in `~/.alphabet-categories/save.json` on that device. Install dependencies before going offline.

## Play

- Add players and choose colors; the game supports up to eight players.
- Use the five default categories or add your own.
- Choose 30, 60, or 90 seconds, or turn the timer off.
- Optionally skip Q, X, and Z, spin categories randomly, or set a round limit.
- Pass one device around. Each player gets a unique letter on their turn.
- Vote answers up or down; only accepted answers earn a point.
- The game ends when eligible letters run out or the selected number of complete player rounds is reached. Ties share the win.
- Locally generated sound effects can be muted.

## Project layout

```text
app.py                         Python/Streamlit UI and local game flow
alphabet_categories/game.py    Pure game rules, independent of the UI
alphabet_categories/storage.py Device-local JSON save/load
tests/test_game.py             Offline rule tests using unittest
requirements.txt               Streamlit UI dependency
```

## Verify game rules offline

Tests use Python's standard library and fabricated player names and answers:

```sh
python -m unittest discover -s tests -v
```

The tests cover one-time letter draws, excluded letters, accepted-answer scoring, both game-ending conditions, and winner selection including ties.

## Privacy and network behavior

The app runs on the local computer and stores data in that user's home folder. It does not transmit player names, categories, answers, or scores to a service. No real personal data is needed for development or testing; test fixtures use made-up names and answers.

The project is licensed under the [MIT License](LICENSE).
