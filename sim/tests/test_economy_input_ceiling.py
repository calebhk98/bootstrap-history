"""A producer never offers more for an input than the run is worth at the input prices it now sees."""

QUICK_TOPIC = True

import unittest

from sim.economy import producers
from sim.economy.types import Recipe

FARM = Recipe("farm", {"grain": 10.0}, {"seed": 2.0}, {"hand": 5.0})


class View:
    year = 3

    def __init__(self, prices, wages):
        self.prices, self.wages = prices, wages

    def price(self, good, area):
        return self.prices.get(good)

    def wage(self, trade, area):
        return self.wages.get(trade)

    def interest_rate(self, currency):
        return 0.05

    def area_of(self, good, tile):
        return "area"

    def currency_of(self, area):
        return "coin"

    def basket_price_level(self, currency):
        return 1.0

    def expected_inflation(self, currency):
        return 0.0

    def cash(self, agent, currency):
        return 0.0

    def stock(self, agent, good, tile):
        return 0.0


def farmer(**changes):
    base = dict(agent_id="f1", owner="lord", recipe_id="farm", tile="t", capacity_runs=10.0)
    base.update(changes)
    return producers.Producer(**base)


class InputCeilingTests(unittest.TestCase):
    def test_a_run_that_no_longer_pays_at_the_live_input_price_bids_no_more_than_that_price(self):
        # the producer still expects seed at 1 and grain at 2 (a run earns 20 against 7), but seed now sells at 10,
        # where a run costs 25 and earns 20: it has no margin to offer for seed
        who = farmer(expected_prices={"grain": 2.0, "seed": 1.0})
        plan = producers.plan(who, FARM, View({"grain": 2.0, "seed": 10.0}, {"hand": 1.0}), 1e6)
        self.assertGreater(plan.runs, 0.0)
        seed = [bid for bid in plan.bids if bid.good == "seed"][0]
        self.assertLessEqual(seed.maximum_price, 10.0 + 1e-9)

    def test_a_run_that_pays_at_the_live_input_price_bids_up_to_the_price_that_breaks_even(self):
        who = farmer(expected_prices={"grain": 2.0, "seed": 1.0})
        plan = producers.plan(who, FARM, View({"grain": 2.0, "seed": 1.0}, {"hand": 1.0}), 1e6)
        seed = [bid for bid in plan.bids if bid.good == "seed"][0]
        self.assertGreater(seed.maximum_price, 1.0)


if __name__ == "__main__":
    unittest.main()
