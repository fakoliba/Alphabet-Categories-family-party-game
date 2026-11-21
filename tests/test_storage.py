import tempfile
import unittest
from pathlib import Path

from alphabet_categories.storage import load_data, save_data


class StorageTests(unittest.TestCase):
    def test_game_data_round_trips_to_local_json_file(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            path = Path(temporary_dir) / "save.json"
            sample = {
                "settings": {"players": [{"name": "Avery"}]},
                "active_game": {"used_letters": ["A"]},
                "past_games": [{"winner": "Avery"}],
            }
            save_data(sample, path)
            self.assertEqual(load_data(path), sample)


if __name__ == "__main__":
    unittest.main()
