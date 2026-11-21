# Alphabet Categories

An offline-first family party game. Pick a letter, name something in a category, and let everyone at the table vote.

## Run it

The app uses only Python's standard library. It does not require Streamlit, a package install, an account, analytics, remote fonts, or internet access. A browser displays the interface, while Python runs the game locally.

```sh
python3 --version
```

Start the app on the same computer:

```sh
python3 app.py
```

The app opens at `http://127.0.0.1:8765` in your browser. It binds only to the local computer. Game settings, player names, and past results are stored in `~/.alphabet-categories/save.json` on that device. No package installation is needed, so it can be started on a computer that has no internet connection.

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
app.py                         Python standard-library local web app and game flow
alphabet_categories/game.py    Pure game rules, independent of the UI
alphabet_categories/storage.py Device-local JSON save/load
tests/test_game.py             Offline rule tests using unittest
```

## Verify game rules offline

Tests use Python's standard library and fabricated player names and answers:

```sh
python -m unittest discover -s tests -v
```

The tests cover one-time letter draws, excluded letters, accepted-answer scoring, both game-ending conditions, and winner selection including ties.

## Privacy and network behavior

The app runs on the local computer and stores data in that user's home folder. It does not transmit player names, categories, answers, or scores to a service. The server listens only on `127.0.0.1`, and request logging is disabled so names and answers are not printed to the terminal. No real personal data is needed for development or testing; test fixtures use made-up names and answers.

The project is licensed under the [MIT License](LICENSE).
