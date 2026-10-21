"""PINS CURRENT BEHAVIOUR, Complaints/710: a founder concern's takings are its physical yearly output at the ask the
home sellers show, with no check that buyers exist for that quantity at that price. The rule is called on built
baskets (sim/engine/node_revenue_market.py, sim/world/plant_figures.py), not a game. Fix this test with 710."""
QUICK_TOPIC = True

import unittest

from sim.engine import node_revenue_market
from sim.world import plant_figures
import types


def baskets(tonnes):
    return types.SimpleNamespace(outputs={"acid": tonnes}, purchases={}, energy_sold={}, energy_bought={})


class NoDemandCheckTests(unittest.TestCase):
    COST = 10.0

    def factor(self, ask, tonnes=100.0):
        return node_revenue_market.basket_market_factor({"acid": tonnes}, {}, {"acid": self.COST}, lambda material: ask)

    def test_the_factor_is_the_ask_over_cost_however_far_it_is_above_cost(self):
        self.assertAlmostEqual(self.factor(self.COST), 1.0)
        self.assertAlmostEqual(self.factor(200.0 * self.COST), 200.0)

    def test_the_factor_does_not_depend_on_how_many_tonnes_are_sold(self):
        self.assertAlmostEqual(self.factor(50.0, tonnes=1.0), self.factor(50.0, tonnes=1.0e6))

    def test_takings_grow_in_proportion_to_tonnes_with_no_buyer_limit(self):
        small = plant_figures.takings(baskets(1.0), {"acid": 50.0})
        large = plant_figures.takings(baskets(1.0e6), {"acid": 50.0})
        self.assertAlmostEqual(large / small, 1.0e6)


if __name__ == "__main__":
    unittest.main()
