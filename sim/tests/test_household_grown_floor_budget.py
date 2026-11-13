"""A floor the household's own plot grew is met before the budget is sized: it is not charged against the cash it spends, so the
money it frees goes to the flexible needs, and what they cannot take is offered to lenders (`households.goods_orders`)."""

QUICK_TOPIC = True

import copy
import unittest

from sim.world import need_basket
from sim.economy import households, households_orders
from sim.tests.test_economy_households import BASKET, NEED_DATA, SPECS, View, budget_total, cohort

PEOPLE = 100.0
FOOD_FLOOR_UNITS = 200.0 * PEOPLE
CASH = 200000.0
TARGET = 1000.0
MARGIN = 1.0 + households_orders.FLOOR_BUDGET_PRICE_MARGIN


def orders_for(grown, basket=BASKET):
    return households.goods_orders(cohort(people=PEOPLE, cash_target=TARGET), View(), CASH, 50000.0, basket, SPECS, grown_units=grown)


def lent(orders):
    return sum(offer.amount for offer in orders.funds_offers)


def floor_budget(orders):
    return sum(bid.floor_quantity * bid.reference_price for bid in orders.bids) * MARGIN


def satiated_basket():
    data = copy.deepcopy(NEED_DATA)
    data["needs"]["food"]["satiation_multiple_of_floor"] = 1.0
    for need_id in ("clothing", "tools", "spice"):
        data["needs"][need_id]["satiation_per_capita_per_year"] = 1.0
    return need_basket.make_basket(data, {})


class GrownFloorBudgetTests(unittest.TestCase):
    def test_a_grown_food_floor_is_not_bought(self):
        grain = next(bid for bid in orders_for({"food": FOOD_FLOOR_UNITS}).bids if bid.good == "grain")
        self.assertEqual(grain.floor_quantity, 0.0)

    def test_the_money_a_grown_floor_frees_funds_the_flexible_needs(self):
        bought, grown = orders_for({}), orders_for({"food": FOOD_FLOOR_UNITS})
        freed = floor_budget(bought)
        flexible_bought = budget_total(bought) - freed
        flexible_grown = budget_total(grown) - floor_budget(grown)
        self.assertGreater(flexible_grown - flexible_bought, 0.9 * freed)

    def test_bids_savings_and_target_account_for_the_cash_a_grown_floor_frees(self):
        grown = orders_for({"food": FOOD_FLOOR_UNITS})
        self.assertAlmostEqual(budget_total(grown) + lent(grown) + TARGET, CASH, delta=1.0)

    def test_the_freed_money_is_offered_to_lenders_when_the_flexible_needs_are_satiated(self):
        basket = satiated_basket()
        bought, grown = orders_for({}, basket), orders_for({"food": FOOD_FLOOR_UNITS}, basket)
        freed = floor_budget(bought)
        self.assertGreater(freed, 0.0)
        self.assertAlmostEqual(lent(grown) - lent(bought), freed, delta=0.01 * freed)


if __name__ == "__main__":
    unittest.main()
