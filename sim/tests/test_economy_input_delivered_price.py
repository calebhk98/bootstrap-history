"""A maker bids for an input from the price the input last cleared at in its market, not only from the
remembered price, which a thin trade moves slowly: otherwise it is outbid every year while its plan
assumes the input is cheap."""

QUICK_TOPIC = True

import unittest

from sim.economy import producers
from sim.economy.market_memory import MarketMemory
from sim.economy.types import Recipe

FARM = Recipe("farm", {"grain": 10.0}, {"seed": 2.0}, {"hand": 5.0})
BREAK_EVEN_SEED_PRICE = (20.0 - 5.0) / 2.0          # a run earns 20, wages 5, two seed a run


class View:
    year = 3

    def __init__(self, prices, cleared=None):
        self.prices, self.cleared = prices, cleared

    def price(self, good, area):
        return self.prices.get(good)

    def wage(self, trade, area):
        return 1.0

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


class ViewWithClearing(View):
    def cleared_price(self, good, area):
        return (self.cleared or {}).get(good)


def farmer():
    return producers.Producer("f1", "lord", "farm", "t", 10.0, expected_prices={"grain": 2.0, "seed": 1.0})


def seed_bid(plan):
    return [bid for bid in plan.bids if bid.good == "seed"][0]


class DeliveredInputPriceTests(unittest.TestCase):
    def test_the_reference_and_ceiling_rise_to_the_price_the_input_cleared_at(self):
        view = ViewWithClearing({"grain": 2.0, "seed": 1.0}, cleared={"seed": 3.0})
        bid = seed_bid(producers.plan(farmer(), FARM, view, 1e6))
        self.assertAlmostEqual(bid.reference_price, 3.0)
        self.assertGreaterEqual(bid.maximum_price, 3.0)
        self.assertLessEqual(bid.maximum_price, BREAK_EVEN_SEED_PRICE * 1.01)

    def test_a_cleared_price_below_the_remembered_one_changes_nothing(self):
        view = ViewWithClearing({"grain": 2.0, "seed": 1.0}, cleared={"seed": 0.5})
        self.assertAlmostEqual(seed_bid(producers.plan(farmer(), FARM, view, 1e6)).reference_price, 1.0)

    def test_a_view_that_reports_no_clearing_price_plans_from_the_remembered_price(self):
        view = View({"grain": 2.0, "seed": 1.0})
        self.assertAlmostEqual(seed_bid(producers.plan(farmer(), FARM, view, 1e6)).reference_price, 1.0)

    def test_an_input_cleared_above_what_the_run_can_pay_is_not_bid_above_break_even(self):
        view = ViewWithClearing({"grain": 2.0, "seed": 1.0}, cleared={"seed": 30.0})
        plan = producers.plan(farmer(), FARM, view, 1e6)
        for bid in plan.bids:
            self.assertLessEqual(bid.maximum_price, max(bid.reference_price, BREAK_EVEN_SEED_PRICE) + 1e-9)

    def test_next_years_expectation_of_an_input_follows_the_price_it_cleared_at(self):
        view = ViewWithClearing({"grain": 2.0, "seed": 1.0}, cleared={"seed": 5.0})
        expected = producers.next_expectations(farmer(), FARM, view)["seed"]
        plain = producers.next_expectations(farmer(), FARM, View({"grain": 2.0, "seed": 1.0}))["seed"]
        self.assertGreater(expected, plain)

    def test_the_memory_keeps_the_price_of_a_market_that_traded_and_forgets_one_that_did_not(self):
        memory = MarketMemory()
        memory.note_cleared("seed|area", 4.0, 10.0)
        self.assertEqual(memory.cleared_prices["seed|area"], 4.0)
        memory.note_cleared("seed|area", 5.0, 0.0)
        self.assertNotIn("seed|area", memory.cleared_prices)


if __name__ == "__main__":
    unittest.main()
