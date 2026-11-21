(function (root, factory) {
  const game = factory();
  if (typeof module === "object" && module.exports) module.exports = game;
  if (root) root.AlphabetGame = game;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split("");
  const HARD_LETTERS = ["Q", "X", "Z"];
  const DEFAULT_CATEGORIES = ["Country", "Capital City", "Fruit", "Car Brand", "Animal"];

  function createGame(options) {
    const players = (options.players || []).map((player, index) => ({
      id: player.id || `player-${index + 1}`,
      name: String(player.name || `Player ${index + 1}`).trim(),
      color: player.color || "#f97316",
    }));
    const categories = (options.categories || DEFAULT_CATEGORIES)
      .map((category) => String(category).trim())
      .filter(Boolean);
    if (!players.length) throw new Error("Add at least one player to start.");
    if (!categories.length) throw new Error("Choose at least one category.");

    const roundLimit = Number(options.roundLimit) > 0 ? Number(options.roundLimit) : null;
    return {
      status: "playing",
      settings: {
        players,
        categories,
        timerSeconds: [0, 30, 60, 90].includes(Number(options.timerSeconds))
          ? Number(options.timerSeconds)
          : 60,
        excludeHardLetters: Boolean(options.excludeHardLetters),
        categoryMode: options.categoryMode === "spin" ? "spin" : "sequence",
        roundLimit,
        soundMuted: Boolean(options.soundMuted),
      },
      usedLetters: [],
      history: [],
      scores: Object.fromEntries(players.map((player) => [player.id, 0])),
      pendingTurn: null,
      createdAt: new Date().toISOString(),
      completedAt: null,
    };
  }

  function eligibleLetters(state) {
    return ALPHABET.filter((letter) =>
      !state.usedLetters.includes(letter) &&
      !(state.settings.excludeHardLetters && HARD_LETTERS.includes(letter))
    );
  }

  function shouldFinish(state) {
    const playersPerRound = state.settings.players.length;
    const completedRounds = Math.floor(state.history.length / playersPerRound);
    return eligibleLetters(state).length === 0 ||
      (state.settings.roundLimit !== null && completedRounds >= state.settings.roundLimit);
  }

  function drawLetter(state, rng = Math.random, now = Date.now()) {
    if (state.status !== "playing" || state.pendingTurn) {
      throw new Error("Finish the current turn before drawing another letter.");
    }
    if (shouldFinish(state)) {
      finishGame(state, now);
      return null;
    }
    const letters = eligibleLetters(state);
    if (!letters.length) {
      finishGame(state, now);
      return null;
    }
    const turnIndex = state.history.length;
    const player = state.settings.players[turnIndex % state.settings.players.length];
    const categoryIndex = state.settings.categoryMode === "spin"
      ? Math.floor(rng() * state.settings.categories.length)
      : turnIndex % state.settings.categories.length;
    const letterIndex = Math.min(letters.length - 1, Math.floor(rng() * letters.length));
    const letter = letters[Math.max(0, letterIndex)];
    state.usedLetters.push(letter);
    state.pendingTurn = {
      turnNumber: turnIndex + 1,
      roundNumber: Math.floor(turnIndex / state.settings.players.length) + 1,
      playerId: player.id,
      letter,
      category: state.settings.categories[categoryIndex],
      startedAt: now,
      answerDraft: "",
    };
    return state.pendingTurn;
  }

  function submitAnswer(state, answer, accepted, now = Date.now()) {
    if (state.status !== "playing" || !state.pendingTurn) {
      throw new Error("There is no answer waiting to be recorded.");
    }
    const pending = state.pendingTurn;
    const player = state.settings.players.find((entry) => entry.id === pending.playerId);
    const record = {
      ...pending,
      playerName: player.name,
      answer: String(answer || "").trim(),
      accepted: Boolean(accepted),
      points: accepted ? 1 : 0,
      completedAt: now,
    };
    state.history.push(record);
    if (record.accepted) state.scores[record.playerId] += 1;
    state.pendingTurn = null;
    if (shouldFinish(state)) finishGame(state, now);
    return record;
  }

  function finishGame(state, now = Date.now()) {
    state.status = "complete";
    state.completedAt = new Date(now).toISOString();
    state.pendingTurn = null;
    return state;
  }

  function winners(state) {
    const highest = Math.max(0, ...Object.values(state.scores));
    return state.settings.players.filter((player) => state.scores[player.id] === highest);
  }

  function scoreboard(state) {
    return state.settings.players
      .map((player) => ({ ...player, score: state.scores[player.id] || 0 }))
      .sort((left, right) => right.score - left.score || left.name.localeCompare(right.name));
  }

  return {
    ALPHABET,
    HARD_LETTERS,
    DEFAULT_CATEGORIES,
    createGame,
    eligibleLetters,
    shouldFinish,
    drawLetter,
    submitAnswer,
    winners,
    scoreboard,
  };
});
