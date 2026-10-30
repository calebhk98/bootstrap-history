"""A bid ceiling or an ask quoted by a market that did not trade pulls a producer's expectation no further than the band
around what a unit costs; a price that traded moves it freely (Complaints/473 Update 12)."""

QUICK_TOPIC = True

import unittest

from sim.economy import ask_adjust, planning_price, producers
from sim.economy.market_memory import PRICE_TRADED
from sim.economy.types import QUOTE_BEST_UNFILLED_BID, QUOTE_COST_COVERING, QUOTE_LOWEST_UNFILLED_ASK, Recipe

MEAL = Recipe("meal", {"meal": 1000.0}, {"flour": 300.0}, {"cook": 40.0})
FLOUR_PRICE, COOK_WAGE = 1.0, 0.5
UNIT_COST = (300.0 * FLOUR_PRICE + 40.0 * COOK_WAGE) / 1000.0
INPUT_SHARE = 300.0 * FLOUR_PRICE / (300.0 * FLOUR_PRICE + 40.0 * COOK_WAGE)


class View:
    year = 3

    def __init__(self, price, kind):
        self.meal_price, self.kind = price, kind

    def price(self, good, area):
        return {"meal": self.meal_price, "flour": FLOUR_PRICE}.get(good)

    def price_kind(self, good, area):
        return self.kind if good == "meal" else PRICE_TRADED

    def wage(self, trade, area):
        return COOK_WAGE

    def interest_rate(self, currency):
        return 0.0

    def area_of(self, good, tile):
        return "area"

    def currency_of(self, area):
        return "coin"

    def basket_price_level(self, currency):
        return 1.0

    def expected_inflation(self, currency):
        return 0.0

    def stock(self, agent, good, tile):
        return 0.0


def maker(expected_meal):
    return producers.Producer("m", "owner", "meal", "t", 10.0, last_runs=0.0,
                              expected_prices={"meal": expected_meal, "flour": FLOUR_PRICE})


class HeldToBandTests(unittest.TestCase):
    def test_a_quote_cannot_lift_an_expectation_past_the_band_edge(self):
        edge = ask_adjust.band_edge(UNIT_COST, INPUT_SHARE)
        self.assertAlmostEqual(planning_price.held_to_band(500.0, 0.1, UNIT_COST, INPUT_SHARE), edge)

    def test_a_quote_inside_the_band_passes(self):
        self.assertEqual(planning_price.held_to_band(UNIT_COST, 0.1, UNIT_COST, INPUT_SHARE), UNIT_COST)

    def test_a_quote_never_cuts_an_expectation_that_stands_above_the_band(self):
        self.assertEqual(planning_price.held_to_band(500.0, 4.0, UNIT_COST, INPUT_SHARE), 4.0)

    def test_with_no_unit_cost_the_expectation_is_left_alone(self):
        self.assertEqual(planning_price.held_to_band(500.0, 0.1, None, INPUT_SHARE), 500.0)

    def test_only_a_bid_ceiling_or_an_ask_is_a_bare_quote(self):
        self.assertTrue(planning_price.is_bare_quote(View(5.0, QUOTE_BEST_UNFILLED_BID), "meal", "area"))
        self.assertTrue(planning_price.is_bare_quote(View(5.0, QUOTE_LOWEST_UNFILLED_ASK), "meal", "area"))
        self.assertFalse(planning_price.is_bare_quote(View(5.0, QUOTE_COST_COVERING), "meal", "area"))
        self.assertFalse(planning_price.is_bare_quote(View(5.0, PRICE_TRADED), "meal", "area"))


class NextExpectationsTests(unittest.TestCase):
    def test_a_bid_ceiling_far_above_cost_lifts_the_expectation_only_to_the_band_edge(self):
        expected = producers.next_expectations(maker(UNIT_COST), MEAL, View(700.0, QUOTE_BEST_UNFILLED_BID))["meal"]
        self.assertLessEqual(expected, ask_adjust.band_edge(UNIT_COST, INPUT_SHARE) * 1.0001)
        self.assertGreaterEqual(expected, UNIT_COST)

    def test_an_ask_far_above_cost_lifts_the_expectation_only_to_the_band_edge(self):
        expected = producers.next_expectations(maker(UNIT_COST), MEAL, View(700.0, QUOTE_LOWEST_UNFILLED_ASK))["meal"]
        self.assertLessEqual(expected, ask_adjust.band_edge(UNIT_COST, INPUT_SHARE) * 1.0001)

    def test_the_same_figure_as_a_traded_price_moves_the_expectation_further(self):
        quoted = producers.next_expectations(maker(UNIT_COST), MEAL, View(700.0, QUOTE_BEST_UNFILLED_BID))["meal"]
        traded = producers.next_expectations(maker(UNIT_COST), MEAL, View(700.0, PRICE_TRADED))["meal"]
        self.assertGreater(traded, 10.0 * quoted)


if __name__ == "__main__":
    unittest.main()
