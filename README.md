# Alphabet Categories

An offline-first family party game. Pick a letter, name something in a category, and let everyone at the table vote.

## Run it

This project has no runtime dependencies, account system, API calls, analytics, or external assets. It can be opened directly from `index.html`. For browsers that restrict local-file storage, start a server on your own computer:

```sh
python3 -m http.server 8000
```

Then open `http://localhost:8000`. The app and its assets are served from the local machine; internet access is not used. Game settings and past results are stored in browser `localStorage` on that device.

## Play

- Add players and choose colors; the game supports up to eight players.
- Use the five default categories or add your own.
- Choose 30, 60, or 90 seconds, or turn the timer off.
- Optionally skip Q, X, and Z, spin categories randomly, or set a round limit.
- Pass one device around. Each player gets a unique letter on their turn.
- Vote answers up or down; only accepted answers earn a point.
- The game ends when eligible letters run out or the selected number of complete player rounds is reached. Ties share the win.
- Sound effects are generated locally and can be muted.

## Project layout

```text
index.html       App shell and local script/style references
styles.css       Responsive, kid-friendly interface
src/game.js      Pure game rules; no browser or network dependencies
src/storage.js   Device-local save/load for settings and game history
src/app.js       Setup, pass-and-play UI, timer, scoreboard, and history
tests/game.test.js  Offline rule tests using Node's built-in test runner
```

## Verify game rules offline

Node.js is needed only to run the test suite. There are no packages to install:

```sh
npm test
```

The tests cover one-time letter draws, excluded letters, accepted-answer scoring, both game-ending conditions, and tied winners. Test player names and answers are fabricated.

## Privacy and network behavior

The game does not send player names, categories, answers, or scores anywhere. There are no OpenAI integrations, online job feeds, remote fonts, or third-party scripts. Data stays in the browser profile on the device. Clearing that browser's site data removes saved games.

The project is licensed under the [MIT License](LICENSE).
