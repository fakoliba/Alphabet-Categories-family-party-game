(function () {
  const Game = window.AlphabetGame;
  const Storage = window.AlphabetStorage;
  const app = document.getElementById("app");
  const soundToggle = document.getElementById("sound-toggle");
  const liveRegion = document.getElementById("live-region");
  const palette = ["#f97316", "#2563eb", "#16a085", "#d9468f", "#8b5cf6", "#ca8a04", "#0f9b8e", "#ef4444"];
  let saved = Storage.load();
  let setupError = "";
  let storageWarning = "";
  let savedSettings = saved.settings || {
    players: [
      { id: "player-1", name: "Player 1", color: palette[0] },
      { id: "player-2", name: "Player 2", color: palette[1] },
    ],
    categories: [...Game.DEFAULT_CATEGORIES],
    timerSeconds: 60,
    excludeHardLetters: false,
    categoryMode: "sequence",
    roundLimit: null,
    soundMuted: false,
  };
  let game = saved.activeGame || null;
  let timerInterval = null;
  let audioContext = null;

  function esc(value) {
    return String(value).replace(/[&<>"']/g, (char) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    })[char]);
  }

  function persist() {
    saved.settings = savedSettings;
    saved.activeGame = game;
    try {
      Storage.save(saved);
      storageWarning = "";
    } catch {
      storageWarning = "This browser could not save the game on this device.";
    }
    updateSoundButton();
  }

  function activeMuted() {
    return game ? game.settings.soundMuted : Boolean(savedSettings.soundMuted);
  }

  function updateSoundButton() {
    const muted = activeMuted();
    soundToggle.textContent = muted ? "🔇" : "🔊";
    soundToggle.setAttribute("aria-label", muted ? "Turn sounds on" : "Mute sounds");
    soundToggle.title = muted ? "Turn sounds on" : "Mute sounds";
  }

  function playTone(frequency = 550, duration = .1) {
    if (activeMuted()) return;
    try {
      audioContext ||= new window.AudioContext();
      const oscillator = audioContext.createOscillator();
      const gain = audioContext.createGain();
      oscillator.type = "sine";
      oscillator.frequency.value = frequency;
      gain.gain.setValueAtTime(.08, audioContext.currentTime);
      gain.gain.exponentialRampToValueAtTime(.001, audioContext.currentTime + duration);
      oscillator.connect(gain);
      gain.connect(audioContext.destination);
      oscillator.start();
      oscillator.stop(audioContext.currentTime + duration);
    } catch { /* Sound is optional; the game remains fully playable. */ }
  }

  function announce(message) {
    liveRegion.textContent = message;
  }

  function finishAndArchive() {
    if (!game || game.status !== "complete") return;
    if (!saved.pastGames.some((entry) => entry.gameId === game.gameId)) {
      saved.pastGames.unshift(game);
      saved.pastGames = saved.pastGames.slice(0, 25);
    }
  }

  function setupMarkup() {
    const players = savedSettings.players || [];
    const categories = savedSettings.categories || [...Game.DEFAULT_CATEGORIES];
    const playerRows = players.map((player, index) => `
      <div class="player-row">
        <input class="player-name" aria-label="Player ${index + 1} name" maxlength="28" value="${esc(player.name)}" placeholder="Player ${index + 1}" />
        <input class="player-color" aria-label="Player ${index + 1} color" type="color" value="${esc(player.color || palette[index % palette.length])}" />
        <button class="remove-button remove-player" type="button" aria-label="Remove player ${index + 1}" ${players.length <= 1 ? "disabled" : ""}>×</button>
      </div>`).join("");
    const categoryChips = categories.map((category, index) => `
      <span class="category-chip">${esc(category)}<button type="button" class="remove-category" data-index="${index}" aria-label="Remove ${esc(category)}">×</button></span>`).join("");
    const recent = saved.pastGames.slice(0, 4).map((past) => {
      const names = Game.winners(past).map((winner) => winner.name).join(" & ");
      return `<div class="history-item"><b>${esc(names)}</b> won · ${past.history.length} turns · ${new Date(past.completedAt).toLocaleDateString()}</div>`;
    }).join("");

    app.innerHTML = `
      <section class="hero">
        <div class="eyebrow">A family word game</div>
        <h1>Pick a letter.<br />Name your answer!</h1>
        <p>Take turns, think fast, and see who can name the most things before the alphabet runs out.</p>
      </section>
      <div class="layout">
        <section class="card">
          <div class="section-head"><h2>Who's playing?</h2><button id="add-player" class="mini-button" type="button">+ Add player</button></div>
          <div id="players">${playerRows}</div>
          <div class="field">
            <span class="field-label">Categories</span>
            <div id="categories" class="category-list">${categoryChips}</div>
            <div class="add-category"><input id="new-category" class="text-input" maxlength="32" placeholder="Add your own category" /><button id="add-category" class="mini-button" type="button">Add</button></div>
          </div>
          <div class="options-grid">
            <div class="field"><label for="timer">Turn timer</label><select id="timer">
              <option value="30" ${Number(savedSettings.timerSeconds) === 30 ? "selected" : ""}>30 seconds</option>
              <option value="60" ${Number(savedSettings.timerSeconds) === 60 ? "selected" : ""}>60 seconds</option>
              <option value="90" ${Number(savedSettings.timerSeconds) === 90 ? "selected" : ""}>90 seconds</option>
              <option value="0" ${Number(savedSettings.timerSeconds) === 0 ? "selected" : ""}>No timer</option>
            </select></div>
            <div class="field"><label for="round-limit">Round limit</label><select id="round-limit">
              <option value="0" ${!savedSettings.roundLimit ? "selected" : ""}>Play until letters run out</option>
              <option value="3" ${Number(savedSettings.roundLimit) === 3 ? "selected" : ""}>3 rounds</option>
              <option value="5" ${Number(savedSettings.roundLimit) === 5 ? "selected" : ""}>5 rounds</option>
              <option value="10" ${Number(savedSettings.roundLimit) === 10 ? "selected" : ""}>10 rounds</option>
            </select></div>
          </div>
          <label class="check-row"><input id="exclude-hard" type="checkbox" ${savedSettings.excludeHardLetters ? "checked" : ""} /> Skip tricky letters Q, X, and Z</label>
          <label class="check-row"><input id="category-spin" type="checkbox" ${savedSettings.categoryMode === "spin" ? "checked" : ""} /> Spin categories at random</label>
          ${setupError ? `<p class="error" role="alert">${esc(setupError)}</p>` : ""}
          ${storageWarning ? `<p class="hint" role="status">${esc(storageWarning)}</p>` : ""}
          <button id="start-game" class="primary-button wide" type="button">Start the game →</button>
          <p class="hint">Everything stays on this device. No account or internet connection needed.</p>
        </section>
        <aside class="card">
          <h2>How to play</h2>
          <p class="hint">1. Pass the device to the player shown.</p>
          <p class="hint">2. Draw a letter and name something in the category.</p>
          <p class="hint">3. Everyone votes. Accepted answers earn a point.</p>
          <p class="hint">Each letter is used once. Play until the alphabet runs out or your round limit is reached.</p>
          ${recent ? `<hr /><h2>Recent winners</h2><div class="history-list">${recent}</div>` : ""}
        </aside>
      </div>`;
    bindSetupEvents();
  }

  function collectSetup() {
    const playerRows = [...app.querySelectorAll(".player-row")];
    const players = playerRows.map((row, index) => ({
      id: `player-${index + 1}`,
      name: row.querySelector(".player-name").value.trim(),
      color: row.querySelector(".player-color").value,
    }));
    const categories = [...app.querySelectorAll(".category-chip")]
      .map((chip) => chip.childNodes[0].textContent.trim()).filter(Boolean);
    return {
      players,
      categories,
      timerSeconds: Number(app.querySelector("#timer").value),
      excludeHardLetters: app.querySelector("#exclude-hard").checked,
      categoryMode: app.querySelector("#category-spin").checked ? "spin" : "sequence",
      roundLimit: Number(app.querySelector("#round-limit").value) || null,
      soundMuted: Boolean(savedSettings.soundMuted),
    };
  }

  function bindSetupEvents() {
    app.querySelector("#add-player").addEventListener("click", () => {
      const setup = collectSetup();
      if (setup.players.length >= 8) { setupError = "You can add up to 8 players."; render(); return; }
      setup.players.push({ id: `player-${Date.now()}`, name: `Player ${setup.players.length + 1}`, color: palette[setup.players.length % palette.length] });
      savedSettings = { ...savedSettings, ...setup };
      setupError = "";
      render();
    });
    app.querySelectorAll(".remove-player").forEach((button) => button.addEventListener("click", () => {
      const setup = collectSetup();
      const index = [...app.querySelectorAll(".remove-player")].indexOf(button);
      setup.players.splice(index, 1);
      savedSettings = { ...savedSettings, ...setup };
      render();
    }));
    app.querySelector("#add-category").addEventListener("click", () => {
      const input = app.querySelector("#new-category");
      const setup = collectSetup();
      const name = input.value.trim();
      if (!name) return;
      if (setup.categories.some((item) => item.toLowerCase() === name.toLowerCase())) {
        setupError = "That category is already on the list.";
      } else if (name.length > 32) {
        setupError = "Keep category names to 32 characters or fewer.";
      } else {
        setup.categories.push(name);
        savedSettings = { ...savedSettings, ...setup };
        setupError = "";
      }
      render();
    });
    app.querySelectorAll(".remove-category").forEach((button) => button.addEventListener("click", () => {
      const setup = collectSetup();
      setup.categories.splice(Number(button.dataset.index), 1);
      savedSettings = { ...savedSettings, ...setup };
      render();
    }));
    app.querySelector("#start-game").addEventListener("click", () => {
      const setup = collectSetup();
      if (setup.players.some((player) => !player.name)) setupError = "Give every player a name.";
      else if (!setup.categories.length) setupError = "Choose at least one category.";
      else {
        savedSettings = setup;
        try {
          game = Game.createGame(setup);
          game.gameId = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
          setupError = "";
          persist();
          playTone(610, .13);
          render();
          announce("Game started. Draw a letter for the first player.");
          app.focus();
        } catch (error) { setupError = error.message; render(); }
      }
      if (setupError) render();
    });
  }

  function scoreMarkup() {
    return Game.scoreboard(game).map((player) => `
      <div class="score-row"><span class="score-name"><i class="dot" style="background:${esc(player.color)}"></i>${esc(player.name)}</span><strong class="score-value">${player.score}</strong></div>`).join("");
  }

  function historyMarkup() {
    if (!game.history.length) return '<p class="hint">Your turn history will appear here.</p>';
    return [...game.history].reverse().map((turn) => `
      <div class="history-item"><b>Round ${turn.roundNumber}</b> · ${esc(turn.playerName)} · ${turn.letter} / ${esc(turn.category)}${turn.answer ? ` · “${esc(turn.answer)}”` : ""} · ${turn.accepted ? "+1 point" : "no point"}</div>`).join("");
  }

  function boardMarkup() {
    return Game.ALPHABET.map((letter) => {
      const excluded = game.settings.excludeHardLetters && Game.HARD_LETTERS.includes(letter);
      const used = game.usedLetters.includes(letter);
      const drawn = game.pendingTurn && game.pendingTurn.letter === letter;
      const className = ["letter-tile", used ? "used" : "", excluded ? "excluded" : "", drawn ? "just-drawn" : ""].filter(Boolean).join(" ");
      return `<span class="${className}" aria-label="${letter}${used ? ", already used" : excluded ? ", excluded" : ""}">${letter}</span>`;
    }).join("");
  }

  function remainingSeconds() {
    if (!game || !game.pendingTurn || !game.settings.timerSeconds) return null;
    const elapsed = (Date.now() - game.pendingTurn.startedAt) / 1000;
    return Math.max(0, Math.ceil(game.settings.timerSeconds - elapsed));
  }

  function timerMarkup() {
    const remaining = remainingSeconds();
    if (remaining === null) return "";
    return `<div id="timer-display" class="timer ${remaining <= 10 ? "low" : ""}" aria-live="polite">${remaining}</div>`;
  }

  function pendingMarkup() {
    if (!game.pendingTurn) {
      const left = Game.eligibleLetters(game).length;
      return `<div class="turn-panel"><div class="turn-player">Round ${Math.floor(game.history.length / game.settings.players.length) + 1} · ${left} letters left</div><p class="hint">Pass the device to the next player, then draw a letter.</p><button id="draw-letter" class="primary-button" type="button">🎲 Draw a letter</button></div>`;
    }
    const turn = game.pendingTurn;
    const player = game.settings.players.find((entry) => entry.id === turn.playerId);
    return `<div class="turn-panel">
      <div class="turn-player" style="color:${esc(player.color)}">Round ${turn.roundNumber} · ${esc(player.name)}, your turn!</div>
      <div class="big-letter" aria-label="Letter ${turn.letter}">${turn.letter}</div>
      <div class="category-name">Name a ${esc(turn.category.toLowerCase())}</div>
      ${timerMarkup()}
      <div class="answer-wrap"><label for="answer">Answer (optional record)</label><input id="answer" class="text-input" maxlength="100" placeholder="Type it here or answer out loud" value="${esc(turn.answerDraft || "")}" /></div>
      <p class="hint">Everyone votes: did the answer fit the letter and category?</p>
      <div class="vote-row"><button id="accept-answer" class="vote-button accept" type="button">👍 Accept · +1</button><button id="reject-answer" class="vote-button reject" type="button">👎 Reject · 0</button></div>
      <p id="time-message" class="hint" role="status">${remainingSeconds() === 0 ? "Time is up! Finish the vote." : ""}</p>
    </div>`;
  }

  function winnerMarkup() {
    const winners = Game.winners(game);
    const names = winners.map((player) => player.name);
    const tied = names.length > 1;
    const confetti = Array.from({ length: 24 }, (_, index) => `<i class="confetti" style="left:${(index * 37) % 100}%;background:${palette[index % palette.length]};animation-delay:${(index % 9) * -.3}s"></i>`).join("");
    return `<section class="card winner-card">${confetti}<div class="eyebrow">${tied ? "It's a tie!" : "We have a winner!"}</div><div class="winner-names">${names.map(esc).join(" & ")}</div><p>Great game! You played ${game.history.length} turns and scored ${Math.max(...Object.values(game.scores))} points.</p></section>`;
  }

  function gameMarkup() {
    const complete = game.status === "complete";
    return `
      <div class="section-head"><div><div class="eyebrow">Pass & play</div><h1>${complete ? "Game complete!" : "The letter board"}</h1></div><button id="change-setup" class="secondary-button" type="button">${complete ? "New game" : "Change setup"}</button></div>
      ${complete ? winnerMarkup() : ""}
      <div class="tile-board" aria-label="Alphabet letter board">${boardMarkup()}</div>
      <div class="layout">
        <section class="card">${complete ? `<div class="turn-panel"><p>All done! Start another game with the same players and settings.</p><button id="play-again" class="primary-button" type="button">Play again</button></div>` : pendingMarkup()}</section>
        <aside class="card"><h2>Scoreboard</h2><div class="score-list">${scoreMarkup()}</div></aside>
      </div>
      <section class="card" style="margin-top:16px"><h2>Round history</h2><div class="history-list">${historyMarkup()}</div></section>
      ${storageWarning ? `<p class="hint" role="status">${esc(storageWarning)}</p>` : ""}`;
  }

  function stopTimer() {
    if (timerInterval) window.clearInterval(timerInterval);
    timerInterval = null;
  }

  function tickTimer() {
    const display = app.querySelector("#timer-display");
    if (!display || !game || !game.pendingTurn) { stopTimer(); return; }
    const remaining = remainingSeconds();
    display.textContent = remaining;
    display.classList.toggle("low", remaining <= 10);
    const message = app.querySelector("#time-message");
    if (message) message.textContent = remaining === 0 ? "Time is up! Finish the vote." : "";
  }

  function render() {
    stopTimer();
    if (game) {
      finishAndArchive();
      persist();
      app.innerHTML = gameMarkup();
      const drawButton = app.querySelector("#draw-letter");
      if (drawButton) drawButton.addEventListener("click", () => {
        try {
          const turn = Game.drawLetter(game);
          if (!turn) { finishAndArchive(); persist(); render(); return; }
          persist();
          playTone(470, .13);
          render();
          const player = game.settings.players.find((entry) => entry.id === turn.playerId);
          announce(`${player.name}, letter ${turn.letter}. Name a ${turn.category}.`);
          app.focus();
        } catch (error) { announce(error.message); }
      });
      const answer = app.querySelector("#answer");
      if (answer) {
        answer.addEventListener("input", () => {
          game.pendingTurn.answerDraft = answer.value;
          persist();
        });
        app.querySelector("#accept-answer").addEventListener("click", () => recordAnswer(true));
        app.querySelector("#reject-answer").addEventListener("click", () => recordAnswer(false));
        timerInterval = window.setInterval(tickTimer, 250);
      }
      const change = app.querySelector("#change-setup");
      change.addEventListener("click", () => {
        if (game.status !== "complete" && !window.confirm("Start over and leave this game? Its turns will not be saved in past games.")) return;
        game = null;
        persist();
        render();
      });
      const playAgain = app.querySelector("#play-again");
      if (playAgain) playAgain.addEventListener("click", () => {
        game = Game.createGame(savedSettings);
        game.gameId = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
        persist();
        render();
      });
    } else {
      app.innerHTML = setupMarkup();
    }
    updateSoundButton();
  }

  function recordAnswer(accepted) {
    const input = app.querySelector("#answer");
    const answer = input ? input.value : "";
    Game.submitAnswer(game, answer, accepted);
    finishAndArchive();
    persist();
    playTone(accepted ? 760 : 250, .13);
    announce(accepted ? "Answer accepted. One point." : "Answer rejected. No point.");
    render();
  }

  soundToggle.addEventListener("click", () => {
    if (game) game.settings.soundMuted = !game.settings.soundMuted;
    else savedSettings.soundMuted = !savedSettings.soundMuted;
    persist();
    updateSoundButton();
  });

  if (game && game.status === "complete") finishAndArchive();
  render();
})();
