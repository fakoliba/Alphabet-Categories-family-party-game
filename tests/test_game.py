import random
import unittest

from alphabet_categories.game import (
    HARD_LETTERS,
    draw_letter,
    eligible_letters,
    new_game,
    submit_answer,
    winners,
)


def settings(**changes):
    value = {
        "players": [
            {"id": "p1", "name": "Avery", "color": "#f97316"},
            {"id": "p2", "name": "Jordan", "color": "#2563eb"},
        ],
        "categories": ["Animal", "Fruit"],
        "timer_seconds": 0,
        "exclude_hard_letters": False,
        "category_mode": "sequence",
        "round_limit": None,
    }
    value.update(changes)
    return value


def play_turn(game, rng, answer="", accepted=False):
    draw_letter(game, rng=rng)
    submit_answer(game, answer, accepted)


class GameRulesTests(unittest.TestCase):
    def test_each_letter_is_drawn_once_until_a_new_game(self):
        game = new_game(settings(players=[{"id": "p1", "name": "Avery"}]))
        rng = random.Random(23)
        while game["status"] == "playing":
            play_turn(game, rng)
        self.assertEqual(len(game["used_letters"]), 26)
        self.assertEqual(len(set(game["used_letters"])), 26)
        reset = new_game(settings(players=[{"id": "p1", "name": "Avery"}]))
        self.assertEqual(reset["used_letters"], [])

    def test_excluded_hard_letters_are_never_drawn(self):
        game = new_game(settings(
            players=[{"id": "p1", "name": "Avery"}],
            exclude_hard_letters=True,
        ))
        rng = random.Random(81)
        while game["status"] == "playing":
            play_turn(game, rng)
        self.assertTrue(HARD_LETTERS.isdisjoint(game["used_letters"]))
        self.assertEqual(len(game["used_letters"]), 23)

    def test_only_accepted_answers_increase_scores(self):
        game = new_game(settings())
        rng = random.Random(9)
        play_turn(game, rng, answer="Ant", accepted=True)
        play_turn(game, rng, answer="No", accepted=False)
        self.assertEqual(game["scores"], {"p1": 1, "p2": 0})

    def test_game_ends_after_round_limit(self):
        game = new_game(settings(round_limit=1))
        rng = random.Random(3)
        play_turn(game, rng)
        self.assertEqual(game["status"], "playing")
        play_turn(game, rng)
        self.assertEqual(game["status"], "complete")
        self.assertEqual(len(game["history"]), 2)

    def test_game_ends_when_eligible_letters_run_out(self):
        game = new_game(settings(
            players=[{"id": "p1", "name": "Avery"}],
            exclude_hard_letters=True,
        ))
        rng = random.Random(123)
        while game["status"] == "playing":
            play_turn(game, rng)
        self.assertEqual(len(eligible_letters(game)), 0)
        self.assertEqual(game["status"], "complete")

    def test_winner_selection_supports_ties(self):
        game = new_game(settings())
        game["scores"] = {"p1": 2, "p2": 2}
        self.assertEqual([player["id"] for player in winners(game)], ["p1", "p2"])

    def test_winner_selection_returns_high_score_only(self):
        game = new_game(settings())
        game["scores"] = {"p1": 3, "p2": 1}
        self.assertEqual([player["id"] for player in winners(game)], ["p1"])


if __name__ == "__main__":
    unittest.main()
