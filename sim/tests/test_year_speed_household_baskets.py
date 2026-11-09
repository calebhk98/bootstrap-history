"""Household baskets are built once per kind and priced once per tile until the market memory is written to; each kept
answer equals a fresh computation."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import household_work_year, households_basket, priced_reads
from sim.world import need_basket
from sim.world.need_basket import make_basket

NEED_DATA = {"needs": {"food": {"surplus_budget_share": 0.5, "subsistence_per_capita_per_year": 10.0},
                       "warmth": {"surplus_budget_share": 0.1, "subsistence_per_capita_per_year": 300.0},
                       "household_work": {"surplus_budget_share": 0.0, "subsistence_per_capita_per_year": 0.0}},
             "goods": {"wheat_kg": {"satisfies": {"food": 1.0}},
                       "barley_kg": {"satisfies": {"food": 0.8}},
                       "cooked_meal_kg": {"satisfies": {"food": 0.3}},
                       "domestic_service_hour": {"satisfies": {"household_work": 1.0}},
                       "wood_kg": {"satisfies": {"warmth": 15.0}}}}
SETUP = types.SimpleNamespace(
    basket_for=lambda tile: make_basket(NEED_DATA, {}), ready_to_eat=frozenset({"cooked_meal_kg"}), hunger_need="food",
    household_work={"days_per_year": 100, "cooking_fuel_mj_per_person_per_day": 2.0}, fuel_need="warmth", work_need="household_work")
PRICES = {"wheat_kg": 2.0, "barley_kg": 1.5, "cooked_meal_kg": 1.0, "domestic_service_hour": 0.4, "wood_kg": 0.1}


class View:
    """A view that keeps reads like the economy's, dropped by `write`, and records the prices it is asked for."""

    def __init__(self, prices):
        self.prices, self.reads, self.asked = dict(prices), {}, []

    def _current(self):
        return self.reads

    def write(self, prices):
        self.prices, self.reads = dict(prices), {}

    def area_of(self, good, tile):
        return "area"

    def offered_price(self, good, area):
        self.asked.append(good)
        return self.prices.get(good)


def fresh(basket, view, tile):
    return list(need_basket.need_prices(basket, lambda good: view.offered_price(good, view.area_of(good, tile))))


class KeptNeedPrices(unittest.TestCase):

    def test_the_kept_list_equals_a_fresh_pricing_and_is_priced_once(self):
        view, basket = View(PRICES), make_basket(NEED_DATA, {})
        first = households_basket.cohort_need_prices(basket, view, "t", ("t", True, 0.0, ()))
        asked = len(view.asked)
        second = households_basket.cohort_need_prices(basket, view, "t", ("t", True, 0.0, ()))
        self.assertIs(first, second)
        self.assertEqual(len(view.asked), asked)
        self.assertEqual(first, fresh(basket, view, "t"))

    def test_a_write_drops_the_kept_list_and_the_new_prices_are_read(self):
        view, basket = View(PRICES), make_basket(NEED_DATA, {})
        before = households_basket.cohort_need_prices(basket, view, "t", ("t", True, 0.0, ()))
        view.write({**PRICES, "wheat_kg": 4.0})
        after = households_basket.cohort_need_prices(basket, view, "t", ("t", True, 0.0, ()))
        self.assertNotEqual(before, after)
        self.assertEqual(after, fresh(basket, view, "t"))

    def test_baskets_that_share_a_need_price_it_alike(self):
        view, basket = View(PRICES), make_basket(NEED_DATA, {})
        hearthless = household_work_year.built_basket(SETUP, "t", False, 0.0, ())
        plain = priced_reads.kept_need_prices(view, lambda: basket, "t", "plain")
        other = priced_reads.kept_need_prices(view, lambda: hearthless, "t", "hearthless")
        self.assertEqual(other, fresh(hearthless, view, "t"))
        shared = [need for need in plain if need.spec.need_id == "household_work"]
        self.assertEqual(shared[0], [need for need in other if need.spec.need_id == "household_work"][0])

    def test_a_view_without_kept_reads_prices_every_time(self):
        view = View(PRICES)
        view._current = None
        basket = make_basket(NEED_DATA, {})
        self.assertEqual(households_basket.cohort_need_prices(basket, view, "t", ("t",)), fresh(basket, view, "t"))


class BuiltBaskets(unittest.TestCase):

    def test_a_cohort_basket_has_the_hired_work_the_fuel_and_not_the_milled_grain(self):
        basket = household_work_year.built_basket(SETUP, "t", True, 3.0, ("wheat_kg",))
        needs = {need.need_id: need for need in basket.needs}
        self.assertEqual(needs["household_work"].subsistence_per_person, 3.0)
        self.assertGreater(needs["warmth"].subsistence_per_person, 300.0)
        self.assertNotIn("wheat_kg", [good for good, _effect in needs["food"].goods])
        self.assertIn("barley_kg", [good for good, _effect in needs["food"].goods])

    def test_a_cohort_with_no_hearth_buys_only_food_that_is_ready_to_eat(self):
        basket = household_work_year.built_basket(SETUP, "t", False, 0.0, ())
        food = next(need for need in basket.needs if need.need_id == "food")
        self.assertEqual([good for good, _effect in food.goods], ["cooked_meal_kg"])

    def test_the_same_signature_is_the_same_object_and_another_setup_starts_afresh(self):
        key = ("t", True, 1.0, ())
        first = household_work_year.kept_basket(SETUP, key)
        self.assertIs(household_work_year.kept_basket(SETUP, key), first)
        self.assertEqual(first, household_work_year.built_basket(SETUP, *key))
        other = types.SimpleNamespace(**vars(SETUP))
        self.assertIsNot(household_work_year.kept_basket(other, key), first)


class BaseBasket(unittest.TestCase):

    def test_a_basket_for_any_hired_work_equals_the_base_with_the_floor_put_on(self):
        for hearth in (True, False):
            for milled in ((), ("wheat_kg",)):
                base = household_work_year.base_basket(SETUP, "t", hearth, milled)
                for hired in (0.0, 0.5, 3.0):
                    self.assertEqual(household_work_year.with_hired_work(SETUP, base, hired),
                                     household_work_year.built_basket(SETUP, "t", hearth, hired, milled))

    def test_no_hired_work_leaves_the_base_whole_and_hired_work_changes_only_the_work_need(self):
        base = household_work_year.base_basket(SETUP, "t", True, ())
        self.assertIs(household_work_year.with_hired_work(SETUP, base, 0.0), base)
        hired = household_work_year.with_hired_work(SETUP, base, 2.0)
        changed = [after.need_id for before, after in zip(base.needs, hired.needs) if before != after]
        self.assertEqual(changed, ["household_work"])


if __name__ == "__main__":
    unittest.main()
