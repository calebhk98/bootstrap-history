"""Grinding as a make-or-buy choice (Complaint 645): a household grinds grain by hand only when its hours cost less
than the milled good, and water and fuel are a fixed load either way."""

QUICK_TOPIC = True

import dataclasses
import types
import unittest

from sim.tests.economy_view_defaults import ViewDefaults
from sim.economy import household_grinding, household_work_year, households, households_work
from sim.world.need_basket import make_basket, priced_need
from sim.economy.households_cohort import Cohort
from sim.economy.market_memory import market_key
from sim.economy.setup import SetupTrade, labour_area
from sim.economy.types import LabourOffer

WORKING_DAYS = 100.0
DATA = {"days_per_year": 365, "tasks": {
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


class View(ViewDefaults):
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
        opening_wages={"labourer": 1.0, "servant": 1.0}, unskilled_trade="labourer", currency_id="coin",
        trades={"labourer": SetupTrade("labourer"), "servant": SetupTrade("servant")},
        household_work=DATA, working_hours_per_year=1000.0, working_days_per_year=WORKING_DAYS, servant_trade="servant", hunger_need="food", fuel_need="warmth", work_need="household_work",
        ready_to_eat=frozenset(), milled_as=household_grinding.milled_as_map(NEED_DATA),
        basket_for=lambda tile: make_basket(NEED_DATA, {}))


def plan(prices, wage_per_hour, held=None, gradual=False, held_share=None, with_share=False):
    area = labour_area("t1")
    worker = Cohort(agent_id="c", tile="t1", income_class=0, people=100.0, working_people=50.0, ownership_share=0.0,
                    ground_by_hand=held or (), food_ground_share=held_share)
    rec = types.SimpleNamespace(cohorts={"c": worker}, labour=types.SimpleNamespace(sold_share_expected={market_key("labourer", area): 1.0}), land=types.SimpleNamespace(titles={"t1": {"c": 1.0}}, tenancies={}))
    offers = [LabourOffer("c", "labourer", area, 500.0, wage_per_hour)]
    planned = household_work_year.cohort_plan(setup(), rec, View({("labourer", area): wage_per_hour, ("servant", area): 1e6}, prices), worker, offers,
                                              gradual=gradual)
    return planned if with_share else planned[:3]


class GrindingChoiceTests(unittest.TestCase):
    def test_a_household_that_can_buy_flour_cheaper_than_its_hours_are_worth_grinds_nearly_nothing(self):
        # by hand: wheat 1.0 plus 5 hours at 1.0 each per unit, 6.0; flour 2.0 is cheaper (the choice is a logit, so the share ground by hand is small rather than nothing)
        hired, own, ground = plan({"wheat_kg": 1.0, "flour_kg": 2.0}, 1.0)
        self.assertLess(dict(ground)["wheat_kg"], 0.01)
        self.assertAlmostEqual(hired, 0.0)
        self.assertAlmostEqual(own, 100.0 * WATER_AND_FUEL_HOURS, delta=0.01 * 100.0 * GRINDING_HOURS)

    def test_a_household_whose_hours_are_cheaper_than_the_milling_grinds_by_hand(self):
        _hired, own, ground = plan({"wheat_kg": 1.0, "flour_kg": 9.0}, 1.0)
        unit_share = household_grinding.unit_shares([("wheat_kg", 1.0, 1.0, 0.5), ("flour_kg", 9.0, 1.0, 0.5)])["wheat_kg"]
        self.assertGreater(dict(ground)["wheat_kg"], 0.99 * unit_share)
        # it still buys a little flour in its mix, so it grinds the rest: most of the load, not all of it
        self.assertGreater(own, 100.0 * (WATER_AND_FUEL_HOURS + 0.9 * GRINDING_HOURS))
        self.assertLess(own, 100.0 * (WATER_AND_FUEL_HOURS + GRINDING_HOURS))

    def test_a_household_with_no_mill_in_reach_grinds_by_hand_at_the_sourced_load(self):
        _hired, own, ground = plan({"wheat_kg": 1.0}, 1000.0)
        self.assertEqual(ground, ())
        self.assertAlmostEqual(own, households_work.hours_needed(100.0, DATA, WORKING_DAYS))
        self.assertAlmostEqual(own, 100.0 * (WATER_AND_FUEL_HOURS + GRINDING_HOURS))

    def test_water_and_fuel_are_charged_whether_it_grinds_or_buys(self):
        _hired, buys, _ground = plan({"wheat_kg": 1.0, "flour_kg": 2.0}, 1.0)
        _hired, grinds, _ground = plan({"wheat_kg": 1.0}, 1.0)
        self.assertGreater(buys, 0.0)
        self.assertAlmostEqual(grinds - buys, 100.0 * GRINDING_HOURS, delta=0.01 * 100.0 * GRINDING_HOURS)

    def test_hours_scale_with_the_share_of_the_food_ground_by_hand(self):
        self.assertAlmostEqual(households_work.hours_per_person_per_year(DATA, WORKING_DAYS, True, 0.4),
                               WATER_AND_FUEL_HOURS + 0.4 * GRINDING_HOURS)
        self.assertAlmostEqual(households_work.hours_per_person_per_year(DATA, WORKING_DAYS, True, 0.0), WATER_AND_FUEL_HOURS)

    def test_a_grain_ground_by_none_is_capped_at_nothing_so_the_household_buys_the_milled_good(self):
        basket = make_basket(NEED_DATA, {})
        food = next(need for need in household_grinding.with_hand_ground(basket, (("wheat_kg", 0.0),), "food").needs if need.need_id == "food")
        self.assertEqual(dict(food.share_limits), {"wheat_kg": 0.0})
        priced = priced_need(food, 1.0 - basket.substitution, {"wheat_kg": 1.0, "flour_kg": 1.5}.get)
        self.assertEqual({good: share for good, _price, _effect, share in priced.goods}["wheat_kg"], 0.0)

    def test_the_cap_is_the_tighter_of_the_share_ground_and_the_grain_s_own_limit(self):
        basket = make_basket(NEED_DATA, {})
        limited = dataclasses.replace(basket, needs=tuple(
            dataclasses.replace(need, share_limits=(("wheat_kg", 0.3),)) if need.need_id == "food" else need for need in basket.needs))
        food = next(need for need in household_grinding.with_hand_ground(limited, (("wheat_kg", 0.5),), "food").needs if need.need_id == "food")
        self.assertEqual(dict(food.share_limits), {"wheat_kg": 0.3})

    def test_the_basket_is_left_whole_when_nothing_else_would_serve(self):
        basket = make_basket({"needs": NEED_DATA["needs"], "goods": {"wheat_kg": NEED_DATA["goods"]["wheat_kg"]}}, {})
        food = next(need for need in household_grinding.with_hand_ground(basket, (("wheat_kg", 0.0),), "food").needs if need.need_id == "food")
        self.assertEqual(food.share_limits, ())

    def test_the_grain_bought_is_continuous_in_the_share_ground_by_hand(self):
        basket = make_basket(NEED_DATA, {})
        previous = None
        for step in range(0, 101):
            capped = household_grinding.with_hand_ground(basket, (("wheat_kg", 0.5 * (1.0 - step / 100.0)),), "food")
            food = next(need for need in capped.needs if need.need_id == "food")
            priced = priced_need(food, 1.0 - basket.substitution, {"wheat_kg": 1.0, "flour_kg": 1.5}.get)
            wheat = {good: share for good, _price, _effect, share in priced.goods}["wheat_kg"]
            if previous is not None:
                self.assertLess(abs(wheat - previous), 0.02)
            previous = wheat
        self.assertEqual(previous, 0.0)

    def test_grain_a_household_grew_and_ate_counts_toward_its_floor_though_it_buys_that_grain_milled(self):
        # Complaint 640: the bids leave the grain out, but what the household ate of it from its own plot is food
        worker = Cohort(agent_id="c", tile="t1", income_class=0, people=100.0, working_people=50.0, ownership_share=0.0,
                        ground_by_hand=(("wheat_kg", 0.0),))
        rec = types.SimpleNamespace(cohorts={"c": worker}, labour=types.SimpleNamespace(sold_share_expected={market_key("labourer", labour_area("t1")): 1.0}), land=types.SimpleNamespace(titles={"t1": {"c": 1.0}}, tenancies={}))
        bidding = household_work_year.cohort_basket(setup(), rec, worker)
        eating = household_work_year.cohort_basket(setup(), rec, worker, buying=False)
        self.assertEqual([dict(need.share_limits) for need in bidding.needs if need.need_id == "food"], [{"wheat_kg": 0.0}])
        self.assertEqual([dict(need.share_limits) for need in eating.needs if need.need_id == "food"], [{}])
        grown = {"wheat_kg": 1000.0}
        self.assertEqual(households.unmet_floor_by_need(worker, grown, View({}, {}), {}, eating).get("food", 0.0), 0.0)


ROWS = [("wheat_kg", 1.0, 1.0, 0.5), ("flour_kg", 2.0, 1.0, 0.5)]   # (good, price, need units a unit gives, spending share)
MILLED_AS = {"wheat_kg": "flour_kg"}


class ContinuousChoiceTests(unittest.TestCase):
    def test_the_bought_share_falls_smoothly_and_monotonically_as_the_hour_value_falls_through_the_crossing(self):
        # by hand a unit costs 1.0 + 5 * hour_value, flour 2.0: they are equal at 0.2
        values = [0.4 - 0.0005 * step for step in range(0, 801)]
        shares = [household_grinding.bought_shares(ROWS, MILLED_AS, 5.0, value)["wheat_kg"] for value in values]
        for before, after in zip(shares, shares[1:]):
            self.assertLessEqual(after, before + 1e-15)
            self.assertLess(before - after, 0.01)
        self.assertGreater(shares[0], 0.9)
        self.assertLess(shares[-1], 0.1)

    def test_the_bought_share_is_a_half_where_the_two_costs_meet(self):
        self.assertAlmostEqual(household_grinding.bought_shares(ROWS, MILLED_AS, 5.0, 0.2)["wheat_kg"], 0.5)

    def test_the_bought_share_changes_by_a_hair_when_the_flour_price_changes_by_a_hair(self):
        dearer = [ROWS[0], ("flour_kg", 2.0 + 1e-9, 1.0, 0.5)]
        gap = household_grinding.bought_shares(ROWS, MILLED_AS, 5.0, 0.2)["wheat_kg"] - household_grinding.bought_shares(dearer, MILLED_AS, 5.0, 0.2)["wheat_kg"]
        self.assertGreater(gap, 0.0)
        self.assertLess(gap, 1e-6)

    def test_far_cheaper_milled_flour_is_nearly_all_bought_and_far_dearer_is_nearly_all_ground(self):
        cheap = [ROWS[0], ("flour_kg", 0.01, 1.0, 0.5)]
        dear = [ROWS[0], ("flour_kg", 100.0, 1.0, 0.5)]
        self.assertGreater(household_grinding.bought_shares(cheap, MILLED_AS, 5.0, 0.2)["wheat_kg"], 0.99)
        self.assertLess(household_grinding.bought_shares(dear, MILLED_AS, 5.0, 0.2)["wheat_kg"], 0.01)

    def test_a_grain_with_no_priced_milled_good_is_not_bought_milled(self):
        self.assertEqual(household_grinding.bought_shares(ROWS[:1], MILLED_AS, 5.0, 0.0), {})

    def test_the_share_ground_by_hand_moves_in_small_steps_with_the_hour_value(self):
        kept = None
        for step in range(0, 801):
            value = 0.4 - 0.0005 * step
            bought = household_grinding.bought_shares(ROWS, MILLED_AS, 5.0, value)
            ground = household_grinding.ground_share(ROWS, MILLED_AS, household_grinding.ground_by_hand(ROWS, MILLED_AS, bought))
            if kept is not None:
                self.assertLess(abs(ground - kept), 0.01)
            kept = ground

    def test_the_share_ground_by_hand_is_the_grain_share_less_what_is_bought_milled(self):
        grain_share = household_grinding.unit_shares(ROWS)["wheat_kg"]
        ground = household_grinding.ground_by_hand(ROWS, MILLED_AS, {"wheat_kg": 0.25})
        self.assertAlmostEqual(household_grinding.ground_share(ROWS, MILLED_AS, ground), 0.75 * grain_share)

    def test_the_food_need_moves_in_small_steps_with_the_share_ground_by_hand(self):
        basket = make_basket(NEED_DATA, {})
        previous = None
        for step in range(0, 101):
            capped = household_grinding.with_hand_ground(basket, (("wheat_kg", 0.4 * (1.0 - step / 100.0)),), "food")
            food = next(need for need in capped.needs if need.need_id == "food")
            self.assertEqual({good for good, _effect in food.goods}, {"wheat_kg", "flour_kg"})
            limit = dict(food.share_limits)["wheat_kg"]
            if previous is not None:
                self.assertLess(abs(limit - previous), 0.01)
            previous = limit
        self.assertAlmostEqual(previous, 0.0)


class GradualStepTests(unittest.TestCase):
    def test_the_overall_share_moves_the_declared_share_of_the_gap_in_a_year(self):
        self.assertAlmostEqual(household_grinding.stepped_overall_share(0.45, 0.02, 0.2), 0.45 + 0.2 * (0.02 - 0.45))

    def test_the_overall_share_rests_when_the_held_and_the_computed_are_equal(self):
        self.assertAlmostEqual(household_grinding.stepped_overall_share(0.3, 0.3, 0.2), 0.3)

    def test_the_overall_share_with_none_held_is_the_computed_one_whole(self):
        self.assertEqual(household_grinding.stepped_overall_share(None, 0.02, 0.2), 0.02)

    def test_the_declared_speed_is_the_default_step_of_the_overall_share(self):
        speed = household_grinding.GRINDING_ADJUSTMENT_SHARE_PER_YEAR
        self.assertAlmostEqual(household_grinding.stepped_overall_share(0.5, 0.0), 0.5 - speed * 0.5)

    def test_a_yearly_decision_counts_housework_at_the_overall_share_moved_part_of_the_way(self):
        *_rest, whole = plan({"wheat_kg": 1.0, "flour_kg": 9.0}, 1.0, with_share=True)
        *_rest, counted = plan({"wheat_kg": 1.0, "flour_kg": 9.0}, 1.0, held_share=0.0, gradual=True, with_share=True)
        speed = household_grinding.GRINDING_ADJUSTMENT_SHARE_PER_YEAR
        self.assertAlmostEqual(counted, speed * whole)

    def test_the_opening_counts_the_overall_share_whole_whatever_was_held(self):
        *_rest, whole = plan({"wheat_kg": 1.0, "flour_kg": 9.0}, 1.0, with_share=True)
        *_rest, counted = plan({"wheat_kg": 1.0, "flour_kg": 9.0}, 1.0, held_share=0.0, gradual=False, with_share=True)
        self.assertEqual(counted, whole)


    def test_the_share_ground_by_hand_moves_the_declared_share_of_the_gap(self):
        stepped = household_grinding.stepped_ground(ROWS, (("wheat_kg", 0.6),), (("wheat_kg", 0.1),), 0.2)
        self.assertAlmostEqual(dict(stepped)["wheat_kg"], 0.6 + 0.2 * (0.1 - 0.6))

    def test_the_declared_speed_is_the_default_step(self):
        stepped = household_grinding.stepped_ground(ROWS, (("wheat_kg", 0.6),), (("wheat_kg", 0.1),))
        speed = household_grinding.GRINDING_ADJUSTMENT_SHARE_PER_YEAR
        self.assertAlmostEqual(dict(stepped)["wheat_kg"], 0.6 + speed * (0.1 - 0.6))

    def test_the_share_ground_by_hand_rests_when_the_choice_equals_the_held_share(self):
        stepped = household_grinding.stepped_ground(ROWS, (("wheat_kg", 0.3),), (("wheat_kg", 0.3),), 0.2)
        self.assertAlmostEqual(dict(stepped)["wheat_kg"], 0.3)

    def test_a_grain_held_no_share_of_starts_from_all_of_its_units_ground_by_hand(self):
        units = household_grinding.unit_shares(ROWS)["wheat_kg"]
        stepped = household_grinding.stepped_ground(ROWS, (), (("wheat_kg", 0.0),), 0.25)
        self.assertAlmostEqual(dict(stepped)["wheat_kg"], 0.75 * units)

    def test_the_opening_takes_the_choice_whole(self):
        _hired, _own, whole = plan({"wheat_kg": 1.0, "flour_kg": 2.0}, 1.0, held=(("wheat_kg", 0.5),), gradual=False)
        _hired, _own, without_history = plan({"wheat_kg": 1.0, "flour_kg": 2.0}, 1.0)
        self.assertEqual(whole, without_history)

    def test_a_yearly_decision_moves_the_declared_share_of_the_way_from_the_held_share(self):
        _hired, _own, whole = plan({"wheat_kg": 1.0, "flour_kg": 2.0}, 1.0)
        held = 0.5
        _hired, _own, gradual = plan({"wheat_kg": 1.0, "flour_kg": 2.0}, 1.0, held=(("wheat_kg", held),), gradual=True)
        speed = household_grinding.GRINDING_ADJUSTMENT_SHARE_PER_YEAR
        self.assertAlmostEqual(dict(gradual)["wheat_kg"], held + speed * (dict(whole)["wheat_kg"] - held))


if __name__ == "__main__":
    unittest.main()
