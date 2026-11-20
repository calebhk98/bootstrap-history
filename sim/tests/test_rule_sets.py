"""rule_sets: a setup's rule set by name, the two sales holds, and the close constants under the clearing rules."""

QUICK_TOPIC = True

import types
import unittest

import numpy

from sim.economy import close_pack, rule_sets
from sim.economy.close_kernel import K_ASK_STEP, K_REGRESS, K_SOLD_OUT
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
    def test_no_hold_to_sales_is_zeros_of_the_same_shape(self):
        held = rule_sets.no_hold_to_sales(numpy.array([3.0, 0.0, 5.0]))
        self.assertEqual(held.tolist(), [0.0, 0.0, 0.0])

    def test_expected_sales_hold_returns_its_argument(self):
        sales = numpy.array([3.0, 0.0, 5.0])
        self.assertIs(rule_sets.expected_sales_hold(sales), sales)


class ConstantsArrayForClearing(unittest.TestCase):
    def test_it_differs_from_the_search_constants_only_at_three_places(self):
        search = close_pack.constants_array()
        clearing = close_pack.constants_array_for_clearing()
        self.assertEqual(clearing.shape, search.shape)
        changed = {K_REGRESS, K_ASK_STEP, K_SOLD_OUT}
        for index in range(len(search)):
            if index not in changed:
                self.assertEqual(clearing[index], search[index])
        self.assertEqual(clearing[K_REGRESS], 0.0)
        self.assertEqual(clearing[K_ASK_STEP], 0.0)
        self.assertLess(clearing[K_SOLD_OUT], 0.0)


if __name__ == "__main__":
    unittest.main()
