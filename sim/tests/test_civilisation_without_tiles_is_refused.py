"""The agent economy is the game's only economy and runs its markets on the tiles a civilisation holds, so a
civilisation that holds none is refused when the game is built, with a message naming where to declare its claim."""
import copy
import random
import unittest

from .harness import NODES, ORDER, S, unopened_sim


class RefusedWithoutTiles(unittest.TestCase):
    def test_a_civilisation_holding_no_tiles_is_refused(self):
        civ = copy.deepcopy(S.load_civ("rome_100ad"))
        civ["home_tiles"] = []
        civ.pop("home_regions", None)
        with self.assertRaises(ValueError) as refused:
            S.Sim(NODES, list(ORDER), random.Random(1), events=False, manual=True, civ=civ)
        self.assertIn("home_tiles", str(refused.exception))
        self.assertIn(civ["id"], str(refused.exception))

    def test_an_unopened_game_stays_unopened_and_answers_with_the_engines_own_figures(self):
        game = unopened_sim()
        self.assertFalse(game.economy.agent.opened())
        self.assertIsNone(game.economy.agent_prices())
        self.assertGreater(game.economy.material_price("wheat_kg"), 0.0)


if __name__ == "__main__":
    unittest.main()
