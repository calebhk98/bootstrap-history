"""A seller left holding goods nobody bought at its ask is brought down to what sells inside the year's clearing
(unsold_search.py), so its expectation follows the market's price and not a yearly markdown."""

QUICK_TOPIC = True

import math
import unittest

from sim.economy import producers
from sim.economy.types import GoodSpec, Recipe

FARM = Recipe("farm", {"grain": 10.0}, {"seed": 2.0}, {"hand": 5.0})


class View:
    year = 3

    def __init__(self, prices, wages, stock=0.0, rate=0.05):
        self.prices, self.wages, self.held, self.rate = prices, wages, stock, rate

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
        return 1000.0

    def stock(self, agent, good, tile):
        return self.held if good == "grain" else 0.0


def seller(**changes):
    base = dict(agent_id="f1", owner="lord", recipe_id="farm", tile="t", capacity_runs=10.0,
                last_runs=1.0, expected_sales=1.0, expected_prices={"grain": 0.7})
    base.update(changes)
    return producers.Producer(**base)


def frozen_market(stock):
    """The market remembers the price the seller already expects: nothing cleared, nothing moved it."""
    return View({"grain": 0.7, "seed": 1.0}, {"hand": 1.0}, stock)


class UnsoldAskTests(unittest.TestCase):
    def test_unsold_output_with_no_price_and_no_expectation_is_left_alone(self):
        unpriced = View({"seed": 1.0}, {"hand": 1.0}, stock=500.0)
        expected = producers.next_expectations(seller(expected_prices={}), FARM, unpriced)
        self.assertNotIn("grain", expected)

    def test_unsold_stock_does_not_lower_the_expectation_between_years(self):
        # the markdown happens inside the year's clearing (unsold_search.py), so the market's price is the signal
        expected = producers.next_expectations(seller(), FARM, frozen_market(stock=500.0))["grain"]
        self.assertAlmostEqual(expected, 0.7)     # the price the market remembers; only a sold-out seller adds a raise

    def test_no_stock_left_keeps_the_expectation(self):
        expected = producers.next_expectations(seller(), FARM, frozen_market(stock=0.0))["grain"]
        self.assertGreater(expected, 0.65)

    def test_a_large_unsold_stock_still_holds_runs_back(self):
        producer = seller(expected_sales=1e-6)
        runs = producers.runs_for_stock(producer, FARM, View({}, {}, stock=50.0 * FARM.outputs["grain"]))
        self.assertEqual(runs, 0.0)


if __name__ == "__main__":
    unittest.main()
