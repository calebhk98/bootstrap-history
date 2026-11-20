"""rule_sets: a setup's rule set by name, the two sales holds, and the close constants under the clearing rules."""

QUICK_TOPIC = True

import types
import unittest

import numpy

from sim.economy import close_pack, rule_sets
from sim.economy.capacity_by_working import CAPACITY_SHARE_MOVED_PER_YEAR
from sim.economy.close_kernel import (K_ASK_STEP, K_COIN_CHARGE, K_COIN_ON_WORKING, K_EXCESS_PAYOUT, K_EXPECT, K_REGRESS, K_SOLD_OUT, K_WORKING_SHARE,
                                      K_WORKING_WEIGHT)
from sim.economy.setup import DEFAULT_RULE_SET


class Of(unittest.TestCase):
    def test_a_named_set_is_returned(self):
        for name in ("search", "clearing"):
            self.assertIs(rule_sets.of(types.SimpleNamespace(rule_set=name)), rule_sets.RULE_SETS[name])

    def test_an_unknown_name_raises(self):
        with self.assertRaises(ValueError):
            rule_sets.of(types.SimpleNamespace(rule_set="no such set"))

    def test_a_setup_that_names_none_runs_the_default_set(self):
        self.assertIs(rule_sets.of(types.SimpleNamespace()), rule_sets.RULE_SETS[DEFAULT_RULE_SET])

    def test_the_default_rule_set_exists(self):
        self.assertIn(DEFAULT_RULE_SET, rule_sets.RULE_SETS)


class SalesHolds(unittest.TestCase):
    def test_hold_to_stock_alone_names_no_sales_for_any_producer(self):
        held = rule_sets.hold_to_stock_alone(numpy.array([3.0, 0.0, 5.0]))
        self.assertEqual(held.shape, (3,))
        self.assertTrue(numpy.isnan(held).all())

    def test_hold_to_stock_alone_holds_a_maker_of_unkept_goods_to_its_expected_sales(self):
        held = rule_sets.hold_to_stock_alone(numpy.array([3.0, 4.0]), numpy.array([False, True]))
        self.assertTrue(numpy.isnan(held[0]))
        self.assertEqual(held[1], 4.0)

    def test_expected_sales_hold_returns_its_argument(self):
        sales = numpy.array([3.0, 0.0, 5.0])
        self.assertIs(rule_sets.expected_sales_hold(sales), sales)


class ConstantsArrayForClearing(unittest.TestCase):
    def test_it_differs_from_the_search_constants_only_where_the_clearing_rules_differ(self):
        search = close_pack.constants_array()
        clearing = close_pack.constants_array_for_clearing()
        self.assertEqual(clearing.shape, search.shape)
        changed = {K_EXPECT, K_ASK_STEP, K_SOLD_OUT, K_WORKING_WEIGHT, K_WORKING_SHARE, K_COIN_ON_WORKING, K_EXCESS_PAYOUT, K_COIN_CHARGE}
        for index in range(len(search)):
            if index not in changed:
                self.assertEqual(clearing[index], search[index])
        self.assertEqual(clearing[K_EXPECT], close_pack.EXPECTATION_SHARE_MOVED_UNDER_CLEARING)
        self.assertEqual(clearing[K_REGRESS], search[K_REGRESS])      # prices keep their pull toward cost
        self.assertEqual(clearing[K_ASK_STEP], 0.0)
        self.assertLess(clearing[K_SOLD_OUT], 0.0)
        self.assertEqual(clearing[K_WORKING_WEIGHT], 1.0)
        self.assertEqual(clearing[K_WORKING_SHARE], CAPACITY_SHARE_MOVED_PER_YEAR)
        self.assertEqual(clearing[K_COIN_ON_WORKING], 1.0)
        self.assertEqual(clearing[K_EXCESS_PAYOUT], close_pack.SPARE_COIN_SHARE_PAID_PER_YEAR)
        self.assertEqual(clearing[K_COIN_CHARGE], 1.0)

    def test_the_search_constants_leave_the_clearing_rules_off(self):
        search = close_pack.constants_array()
        self.assertEqual(search[K_WORKING_WEIGHT], 0.0)
        self.assertEqual(search[K_COIN_ON_WORKING], 0.0)
        self.assertEqual(search[K_EXCESS_PAYOUT], 1.0)


if __name__ == "__main__":
    unittest.main()
