"""Grinding as a make-or-buy choice (Complaint 645): a household grinds grain by hand only when its hours cost less
than the milled good, and water and fuel are a fixed load either way."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import household_grinding, household_work_year, households_work
from sim.economy.households_basket import make_basket
from sim.economy.households_cohort import Cohort
from sim.economy.setup import labour_area
from sim.economy.types import LabourOffer

DATA = {"days_per_year": 100, "tasks": {
    "water_and_fuel": {"needs_hearth": False, "hours_per_adult_woman_per_day": 0.5, "adult_women_per_person": 0.25},
    "grinding": {"needs_hearth": False, "scales_with_ground_grain": True, "hours_per_adult_woman_per_day": 2.0,
                 "adult_women_per_person": 0.25}}}
NEED_DATA = {"needs": {"food": {"surplus_budget_share": 0.5, "subsistence_per_capita_per_year": 10.0},
                       "household_work": {"surplus_budget_share": 0.0, "subsistence_per_capita_per_year": 0.0}},
             "goods": {"wheat_kg": {"satisfies": {"food": 1.0}, "milled_as": "flour_kg"},
                       "flour_kg": {"satisfies": {"food": 1.0}},
                       "domestic_service_hour": {"satisfies": {"household_work": 1.0}}}}
WATER_AND_FUEL_HOURS = 0.5 * 0.25 * 100   # per person: 12.5
GRINDING_HOURS = 2.0 * 0.25 * 100         # per person at the food floor: 50, so 5 hours per need unit of a floor of 10


class View:
    def __init__(self, wages, prices):
        self.wages, self.prices = wages, prices

    def wage(self, trade, area):
        return self.wages.get((trade, area))

    def price(self, good, _area):
        return self.prices.get(good)

    def area_of(self, _good, tile):
        return tile


def setup():
    return types.SimpleNamespace(
        household_work=DATA, working_hours_per_year=1000.0, servant_trade="servant", hunger_need="food", fuel_need="warmth",
        ready_to_eat=frozenset(), milled_as=household_grinding.milled_as_map(NEED_DATA),
        basket_for=lambda tile: make_basket(NEED_DATA, {}))


def plan(prices, wage_per_hour):
    area = labour_area("t1")
    worker = Cohort(agent_id="c", tile="t1", income_class=0, people=100.0, working_people=50.0, ownership_share=0.0)
    rec = types.SimpleNamespace(titles={"t1": {"c": 1.0}}, tenancies={}, cohorts={"c": worker})
    offers = [LabourOffer("c", "labourer", area, 500.0, wage_per_hour)]
    return household_work_year.cohort_plan(setup(), rec, View({("labourer", area): wage_per_hour}, prices), worker, offers, 0.0)


class GrindingChoiceTests(unittest.TestCase):
    def test_a_household_that_can_buy_flour_cheaper_than_its_hours_are_worth_grinds_nothing(self):
        # by hand: wheat 1.0 plus 5 hours at 1.0 each per unit, 6.0; flour 2.0 is cheaper
        hired, own, milled = plan({"wheat_kg": 1.0, "flour_kg": 2.0}, 1.0)
        self.assertEqual(milled, ("wheat_kg",))
        self.assertEqual(hired, 0.0)
        self.assertAlmostEqual(own, 100.0 * WATER_AND_FUEL_HOURS)

    def test_a_household_whose_hours_are_cheaper_than_the_milling_grinds_by_hand(self):
        _hired, own, milled = plan({"wheat_kg": 1.0, "flour_kg": 9.0}, 1.0)
        self.assertEqual(milled, ())
        # it still buys a little flour in its mix, so it grinds the rest: most of the load, not all of it
        self.assertGreater(own, 100.0 * (WATER_AND_FUEL_HOURS + 0.9 * GRINDING_HOURS))
        self.assertLess(own, 100.0 * (WATER_AND_FUEL_HOURS + GRINDING_HOURS))

    def test_a_household_with_no_mill_in_reach_grinds_by_hand_at_the_sourced_load(self):
        _hired, own, milled = plan({"wheat_kg": 1.0}, 1000.0)
        self.assertEqual(milled, ())
        self.assertAlmostEqual(own, households_work.hours_needed(100.0, DATA))
        self.assertAlmostEqual(own, 100.0 * (WATER_AND_FUEL_HOURS + GRINDING_HOURS))

    def test_water_and_fuel_are_charged_whether_it_grinds_or_buys(self):
        _hired, buys, _milled = plan({"wheat_kg": 1.0, "flour_kg": 2.0}, 1.0)
        _hired, grinds, _milled = plan({"wheat_kg": 1.0}, 1.0)
        self.assertGreater(buys, 0.0)
        self.assertAlmostEqual(grinds - buys, 100.0 * GRINDING_HOURS)

    def test_hours_scale_with_the_share_of_the_food_ground_by_hand(self):
        self.assertAlmostEqual(households_work.hours_per_person_per_year(DATA, True, 0.4),
                               WATER_AND_FUEL_HOURS + 0.4 * GRINDING_HOURS)
        self.assertAlmostEqual(households_work.hours_per_person_per_year(DATA, True, 0.0), WATER_AND_FUEL_HOURS)

    def test_the_milled_grain_leaves_the_food_need_so_the_household_buys_the_milled_good(self):
        basket = make_basket(NEED_DATA, {})
        food = next(need for need in household_grinding.without_goods(basket, ("wheat_kg",)).needs if need.need_id == "food")
        self.assertEqual([good for good, _effect in food.goods], ["flour_kg"])

    def test_the_basket_keeps_a_grain_when_nothing_else_would_serve(self):
        basket = make_basket({"needs": NEED_DATA["needs"], "goods": {"wheat_kg": NEED_DATA["goods"]["wheat_kg"]}}, {})
        food = next(need for need in household_grinding.without_goods(basket, ("wheat_kg",)).needs if need.need_id == "food")
        self.assertEqual([good for good, _effect in food.goods], ["wheat_kg"])


if __name__ == "__main__":
    unittest.main()
