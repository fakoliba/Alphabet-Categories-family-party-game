const test = require("node:test");
const assert = require("node:assert/strict");
const Game = require("../src/game.js");

function setup(overrides = {}) {
  return Game.createGame({
    players: [
      { id: "p1", name: "Avery", color: "#f97316" },
      { id: "p2", name: "Jordan", color: "#2563eb" },
    ],
    categories: ["Animal", "Fruit"],
    timerSeconds: 0,
    excludeHardLetters: false,
    ...overrides,
  });
}

test("letters are drawn once each until a new board is created", () => {
  const game = setup({ players: [{ id: "p1", name: "Avery" }] });
  while (game.status === "playing") {
    Game.drawLetter(game, () => 0);
    Game.submitAnswer(game, "", false);
  }
  assert.equal(game.usedLetters.length, 26);
  assert.equal(new Set(game.usedLetters).size, 26);
  const reset = setup({ players: [{ id: "p1", name: "Avery" }] });
  assert.deepEqual(reset.usedLetters, []);
});

test("excluded hard letters are never available to draw", () => {
  const game = setup({ excludeHardLetters: true, players: [{ id: "p1", name: "Avery" }] });
  while (game.status === "playing") {
    const turn = Game.drawLetter(game, () => 0);
    assert.ok(!Game.HARD_LETTERS.includes(turn.letter));
    Game.submitAnswer(game, "", false);
  }
  assert.ok(Game.HARD_LETTERS.every((letter) => !game.usedLetters.includes(letter)));
});

test("only accepted answers increase a player's score", () => {
  const game = setup();
  Game.drawLetter(game, () => 0);
  Game.submitAnswer(game, "Ant", true);
  Game.drawLetter(game, () => 0);
  Game.submitAnswer(game, "Not accepted", false);
  assert.equal(game.scores.p1, 1);
  assert.equal(game.scores.p2, 0);
});

test("the game ends after the configured number of complete rounds", () => {
  const game = setup({ roundLimit: 1 });
  for (let turn = 0; turn < 2; turn += 1) {
    Game.drawLetter(game, () => 0);
    Game.submitAnswer(game, "answer", true);
  }
  assert.equal(game.status, "complete");
  assert.equal(game.history.length, 2);
});

test("the game ends when all eligible letters have been used", () => {
  const game = setup({
    players: [{ id: "p1", name: "Avery" }],
    excludeHardLetters: true,
  });
  while (game.status === "playing") {
    Game.drawLetter(game, () => 0);
    Game.submitAnswer(game, "", false);
  }
  assert.equal(game.usedLetters.length, 23);
  assert.equal(game.status, "complete");
});

test("winner selection includes every player tied for first", () => {
  const game = setup();
  game.scores.p1 = 2;
  game.scores.p2 = 2;
  assert.deepEqual(Game.winners(game).map((player) => player.id), ["p1", "p2"]);
});

test("winner selection returns only the highest-scoring player", () => {
  const game = setup();
  game.scores.p1 = 3;
  game.scores.p2 = 1;
  assert.deepEqual(Game.winners(game).map((player) => player.id), ["p1"]);
});
