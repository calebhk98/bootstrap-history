"""SCENARIO (Complaint 640): Complaint 539: the felled-timber ledger is saved and, in a played year, firewood felling is drawn from it."""
import os
import tempfile
import unittest

from sim.engine.saveload import load_state, save_state
from sim.tests.harness import sim


class WholeGameTests(unittest.TestCase):

    def test_the_felled_stock_round_trips_through_a_save(self):
        game = sim(civ="rome_100ad", events=False)
        tile = next(iter(game.world_map.tiles))
        game.state.economy.forest_felled = {tile: 123.5}
        path = os.path.join(tempfile.mkdtemp(), "save.json")
        save_state(game, path)
        reloaded = sim(civ="rome_100ad", events=False)
        load_state(reloaded, path)
        self.assertEqual(reloaded.state.economy.forest_felled, {tile: 123.5})


if __name__ == "__main__":
    unittest.main()
