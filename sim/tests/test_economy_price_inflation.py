"""Complaints 473 and 641: observed inflation is the weighted median of the goods' price changes, so one thin good whose
price runs away does not drive what households and lenders expect (`currency.price_inflation`)."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import currency
from sim.economy.households_cohort import Cohort
from sim.economy.households_close import close_year
from sim.economy.households_basket import Basket, NeedSpec
from sim.economy.market_memory import MarketMemory


def goods(count, price):
    return {"good%d" % index: price for index in range(count)}


class WeightedMedianInflationTests(unittest.TestCase):
    def test_one_good_at_fifty_times_its_price_among_steady_ones_is_no_inflation(self):
        before = goods(9, 1.0) | {"thin": 1.0}
        now = goods(9, 1.0) | {"thin": 50.0}
        weights = {good: 1.0 for good in before}
        self.assertEqual(currency.price_inflation(now, before, weights), 0.0)
        self.assertGreater(currency.basket_price_level(now, before, weights) - 1.0, 4.0)   # the index it replaces

    def test_a_rise_in_most_of_the_basket_by_weight_is_the_inflation(self):
        before = {"bread": 1.0, "cloth": 1.0, "salt": 1.0}
        now = {"bread": 1.2, "cloth": 1.2, "salt": 1.0}
        self.assertAlmostEqual(currency.price_inflation(now, before, {"bread": 2.0, "cloth": 1.0, "salt": 1.0}), 0.2)

    def test_a_heavy_good_outweighs_the_many_light_ones(self):
        before = goods(5, 1.0) | {"bread": 1.0}
        now = goods(5, 1.0) | {"bread": 2.0}
        weights = {good: 1.0 for good in before} | {"bread": 10.0}
        self.assertAlmostEqual(currency.price_inflation(now, before, weights), 1.0)

    def test_a_good_without_a_price_in_both_years_or_a_weight_is_left_out(self):
        before = {"a": 1.0, "b": 1.0, "c": 1.0}
        now = {"a": 1.1, "c": 9.0, "d": 3.0}
        self.assertAlmostEqual(currency.price_inflation(now, before, {"a": 1.0, "b": 1.0, "c": 0.0, "d": 1.0}), 0.1)

    def test_no_goods_to_compare_is_none_not_zero(self):
        self.assertIsNone(currency.price_inflation({}, {"a": 1.0}, {"a": 1.0}))
        self.assertIsNone(currency.price_inflation({"a": 1.0}, {"a": 1.0}, {}))


class MemoryAndHouseholdsTests(unittest.TestCase):
    def test_memory_keeps_the_observed_inflation_it_was_given_and_expects_after_it(self):
        memory = MarketMemory(basket_price_levels={"coin": 1.0})
        memory.note_basket_price_level("coin", 3.0, observed_inflation=0.1)
        self.assertEqual(memory.observed_inflation["coin"], 0.1)
        self.assertAlmostEqual(memory.expected_inflation["coin"],
                               currency.update_expected_inflation(0.0, 0.1))

    def test_without_one_memory_falls_back_to_the_change_in_the_level(self):
        memory = MarketMemory(basket_price_levels={"coin": 1.0})
        memory.note_basket_price_level("coin", 1.5)
        self.assertAlmostEqual(memory.observed_inflation["coin"], 0.5)

    def test_a_cohort_expects_after_the_observed_inflation_not_the_runaway_level(self):
        need = NeedSpec("food", 250.0, 0.6, (("grain", 1.0),))
        basket = Basket((need,), 0.5, {"food": {"surplus_budget_share": 0.6}})
        view = types.SimpleNamespace(
            currency_of=lambda area: "coin", area_of=lambda good, tile: "area", basket_price_level=lambda money: 5.0,
            observed_inflation=lambda money: 0.02, interest_rate=lambda money: 0.06,
            price=lambda good, area: 1.0, stock=lambda *_arguments: 0.0)
        cohort = Cohort("household:t:0", "t", 0, 100.0, 50.0, 0.5)
        after, _moves = close_year(cohort, {"grain": 25000.0}, view, {}, basket, income_received=100.0, spent=100.0)
        self.assertAlmostEqual(after.expected_inflation, currency.update_expected_inflation(0.0, 0.02))
        self.assertEqual(after.last_basket_price_level, 5.0)


if __name__ == "__main__":
    unittest.main()
