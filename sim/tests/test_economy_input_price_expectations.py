"""A producer plans against the input prices it expects, not only last year's: a one-year spike in an
input's price does not swing its runs, so a chain of producers does not hand a swing down the chain."""

QUICK_TOPIC = True

import unittest

from sim.economy import producers
from sim.economy.types import Recipe

FARM = Recipe("farm", {"grain": 10.0}, {"seed": 2.0}, {"hand": 5.0})


class View:
    year = 3

    def __init__(self, prices, wages=None, rate=0.05):
        self.prices, self.wages, self.rate = prices, wages or {"hand": 1.0}, rate

    def price(self, good, area):
        return self.prices.get(good)

    def wage(self, trade, area):
        return self.wages.get(trade)

    def interest_rate(self, currency):
        return self.rate

    def area_of(self, good, tile):
        return "area"

    def currency_of(self, area):
        return "coin"

    def cash(self, agent, currency):
        return 0.0

    def stock(self, agent, good, tile):
        return 0.0


def farmer(**changes):
    base = dict(agent_id="f1", owner="lord", recipe_id="farm", tile="t", capacity_runs=10.0,
                expected_prices={"grain": 0.9})              # a run earns 9 against 7 at steady prices
    base.update(changes)
    return producers.Producer(**base)


class InputExpectationTests(unittest.TestCase):
    def test_an_input_expectation_moves_part_of_the_way_to_the_latest_price(self):
        producer = farmer(expected_prices={"grain": 0.9, "seed": 1.0})
        updated = producers.next_expectations(producer, FARM, View({"grain": 0.9, "seed": 3.0}))
        share = producers.EXPECTATION_ADJUSTMENT_SHARE
        self.assertAlmostEqual(updated["seed"], 1.0 + share * (3.0 - 1.0))

    def test_an_input_seen_for_the_first_time_is_expected_at_its_latest_price(self):
        updated = producers.next_expectations(farmer(), FARM, View({"grain": 0.9, "seed": 3.0}))
        self.assertAlmostEqual(updated["seed"], 3.0)

    def test_a_one_year_spike_in_an_input_price_cuts_runs_less_when_the_steady_price_is_expected(self):
        spike = View({"grain": 0.9, "seed": 3.0})            # live run cost 6 + 5 = 11 against revenue 9
        forgetful = producers.plan(farmer(), FARM, spike, 1000.0).runs
        remembering = producers.plan(farmer(expected_prices={"grain": 0.9, "seed": 1.0}), FARM, spike, 1000.0).runs
        self.assertGreater(remembering, forgetful + 1.0)

    def test_orders_for_the_input_are_still_priced_at_what_the_market_asks_now(self):
        spike = View({"grain": 0.9, "seed": 3.0})
        plan = producers.plan(farmer(expected_prices={"grain": 0.9, "seed": 1.0}), FARM, spike, 1000.0)
        self.assertGreater(plan.runs, 0.0)
        self.assertAlmostEqual(plan.bids[0].reference_price, 3.0)


if __name__ == "__main__":
    unittest.main()
