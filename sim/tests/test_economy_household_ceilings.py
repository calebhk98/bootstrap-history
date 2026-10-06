"""A cohort's bid for a good is capped at what one household of its class can pay for one unit."""

QUICK_TOPIC = True

import dataclasses
import unittest

from sim.economy import households
from sim.economy.types import GoodSpec
from sim.world.climate_needs import PERSONS_PER_HOUSEHOLD

NEED_DATA = {
    "needs": {
        "food": {"surplus_budget_share": 0.5, "subsistence_per_capita_per_year": 200.0},
        "adornment": {"surplus_budget_share": 0.5},
    },
    "goods": {
        "grain": {"satisfies": {"food": 1.0}},
        "beads": {"satisfies": {"adornment": 1.0}},
        "gold_leaf": {"satisfies": {"adornment": 1.0}},
    },
}
SPECS = {name: GoodSpec(name, 1.0, 0.0, 0.0, name) for name in ("grain", "beads", "gold_leaf")}
BASKET = households.make_basket(NEED_DATA, {})


class View:
    year = 1

    def __init__(self, prices):
        self.prices = prices

    def price(self, good, area):
        return self.prices.get(good)

    def interest_rate(self, currency):
        return 0.05

    def area_of(self, good, tile):
        return "area:" + good

    def currency_of(self, area):
        return "coin"

    def stock(self, agent, good, tile):
        return 0.0


def orders_for(income_per_person, people=100000.0, gold_price=500.0):
    income = income_per_person * people
    cohort = dataclasses.replace(households.Cohort("household:t:0", "t", 0, people, people / 2, 0.3),
                                 last_year_spending=income)
    view = View({"grain": 1.0, "beads": 2.0, "gold_leaf": gold_price})
    return households.goods_orders(cohort, view, income, income, BASKET, SPECS), people


def bid_for(orders, good):
    return next((bid for bid in orders.bids if bid.good == good), None)


class HouseholdCeilingTests(unittest.TestCase):
    def test_a_poor_tier_has_no_bid_for_a_good_dearer_than_its_household_can_pay(self):
        orders, _people = orders_for(income_per_person=260.0)
        self.assertIsNone(bid_for(orders, "gold_leaf"))
        self.assertIsNotNone(bid_for(orders, "beads"))        # its adornment money goes to the cheap good

    def test_a_rich_tier_can_bid_for_the_dear_good(self):
        orders, _people = orders_for(income_per_person=200000.0)
        self.assertIsNotNone(bid_for(orders, "gold_leaf"))

    def test_no_bid_asks_more_than_one_household_earns(self):
        for income_per_person in (260.0, 2000.0, 200000.0):
            orders, _people = orders_for(income_per_person=income_per_person)
            for bid in orders.bids:
                self.assertLessEqual(bid.maximum_price, income_per_person * PERSONS_PER_HOUSEHOLD, bid.good)

    def test_a_dearer_tier_can_pay_more_per_unit(self):
        poor, _people = orders_for(income_per_person=2000.0, gold_price=50.0)
        rich, _people = orders_for(income_per_person=200000.0, gold_price=50.0)
        self.assertLess(bid_for(poor, "gold_leaf").maximum_price, bid_for(rich, "gold_leaf").maximum_price)

    def test_floor_goods_are_never_dropped(self):
        orders, _people = orders_for(income_per_person=150.0)    # cannot cover its food floor
        self.assertIsNotNone(bid_for(orders, "grain"))
        self.assertGreater(bid_for(orders, "grain").floor_quantity, 0.0)


if __name__ == "__main__":
    unittest.main()
