"""SMOKE (Complaint 920): the browser lists a real game's save with the standing and the people the polity and workforce modules
hold. The row's rules are test_save_listing_and_menu_rules."""
import os
import tempfile
import unittest

from sim.engine import settings
from sim.engine.saveload import save_state
from sim.tests.harness import unopened_sim


class ListingOfARealSave(unittest.TestCase):
    def test_a_real_saves_row_carries_the_games_standing_and_people(self):
        game = unopened_sim()
        directory = tempfile.mkdtemp()
        save_state(game, os.path.join(directory, "game.json"))
        row = settings.list_saves(directory)[0]
        self.assertEqual(row["reputation"], game.view("standing")()["reputation"])
        self.assertEqual((row["scholars"], row["artisans"]), (game.view("staff")()["scholars"], game.view("staff")()["artisans"]))


if __name__ == "__main__":
    unittest.main()
