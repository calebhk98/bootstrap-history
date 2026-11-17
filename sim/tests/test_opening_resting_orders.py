"""The opening's household orders are the year's: a floor the own plot grew is met before the budget is sized, the opening holds the
household's income as cash (no purse for a late cut), and the value of the floor it met is spending in kind
(`OwnPlots.resting_orders`). The test calls that one function against `households.goods_orders` with the same inputs."""

QUICK_TOPIC = True

import unittest

from sim.economy import households
from sim.economy.opening_own import OwnPlots
from sim.tests.test_economy_households import BASKET, SPECS, View, cohort

PEOPLE = 100.0
INCOME = 50000.0
FOOD_FLOOR_UNITS = 200.0 * PEOPLE


def plot_that_grows(units):
    own = OwnPlots.__new__(OwnPlots)
    own.in_kind = 0.0
    own.grow = lambda record, household, priced, own_work=None: units
    return own


class RestingOrdersTests(unittest.TestCase):
    def test_a_cohort_with_a_grown_food_floor_makes_the_orders_a_year_makes(self):
        household = cohort(people=PEOPLE, cash_target=1000.0, last_year_income=INCOME)
        priced = households.need_prices(BASKET, View(), household.tile)
        grown = {"food": 0.5 * FOOD_FLOOR_UNITS}

        def make(cash, grown_units=None):
            return households.goods_orders(household, View(), cash, INCOME, BASKET, SPECS, priced, grown_units=grown_units)

        opening = plot_that_grows(grown).resting_orders(None, household, INCOME, BASKET, priced, make)
        self.assertEqual(opening, make(INCOME, grown))


if __name__ == "__main__":
    unittest.main()
