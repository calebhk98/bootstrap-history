"""SCENARIO (civilisation without tiles): a game built for a civilisation holding no tiles is refused. The refusal rule is in test_civilisation_without_tiles_is_refused."""
import copy
import random
import unittest

from .harness import NODES, ORDER, S


class RefusedWithoutTilesScenarios(unittest.TestCase):
    def test_scenario_a_game_built_for_a_civilisation_holding_no_tiles_is_refused(self):
        civ = copy.deepcopy(S.load_civ("rome_100ad"))
        civ["home_tiles"] = []
        civ.pop("home_regions", None)
        with self.assertRaises(ValueError):
            S.Sim(NODES, list(ORDER), random.Random(1), events=False, manual=True, civ=civ)


if __name__ == "__main__":
    unittest.main()
