"""Complaint 659: a good whose only missing input is a worn tool is still makeable at the start, because a short
tool never stops a run (the next tool, then work by hand). Each test calls the rule on built inputs."""
QUICK_TOPIC = True

import unittest

from sim.economy.types import Recipe
from sim.engine.economy_port_closure import makeable_prices
from sim.engine.economy_port_setup import tool_wear_recipes

REGISTRY = {"hand": {"tool_basket": ["iron"], "tool_stock_per_worker": {"iron": 1.0}, "tool_hours_factor_by_hand": 2.0}}
LIVES = {"iron": 4.0}
HOURS_PER_YEAR = 2000.0
PRODUCTION = {"cacao": {"outputs": {"cacao": 1.0}}, "iron": {"outputs": {"iron": 1.0}}, "ore": {"outputs": {"ore": 1.0}}}


def recipes():
    return tool_wear_recipes({"cacao": Recipe("cacao", {"cacao": 1.0}, {"seed": 1.0}, {"hand": HOURS_PER_YEAR}),
                              "iron": Recipe("iron", {"iron": 1.0}, {"ore": 1.0}, {"smith": 1.0})},
                             REGISTRY, LIVES, HOURS_PER_YEAR)


class MakeablePriceTests(unittest.TestCase):
    def test_a_worn_tool_nobody_can_yet_make_does_not_remove_the_good_it_wears_on(self):
        prices = makeable_prices({"cacao": 1.0, "iron": 1.0, "seed": 1.0}, PRODUCTION, recipes())
        self.assertIn("cacao", prices)
        self.assertNotIn("iron", prices)

    def test_a_missing_hard_input_still_removes_the_good(self):
        prices = makeable_prices({"cacao": 1.0, "iron": 1.0}, PRODUCTION, recipes())
        self.assertNotIn("cacao", prices)


if __name__ == "__main__":
    unittest.main()
