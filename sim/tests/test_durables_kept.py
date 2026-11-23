"""A durable a household uses and the store: the search rules count what is held beyond what the year's flow keeps in
use as a store to sell, the clearing rules keep all of a used durable in use and let wear run it down."""

QUICK_TOPIC = True

import unittest

from sim.economy import durable_stock, rule_sets


class StockInUse(unittest.TestCase):
    def test_where_the_spare_is_sold_the_stock_in_use_is_what_the_flow_keeps(self):
        self.assertEqual(durable_stock.stock_in_use(120.0, 500.0, False), 120.0)

    def test_where_durables_are_kept_all_a_household_holds_of_a_good_it_uses_is_in_use(self):
        self.assertEqual(durable_stock.stock_in_use(120.0, 500.0, True), 500.0)

    def test_a_household_that_holds_less_than_its_flow_keeps_counts_what_the_flow_keeps(self):
        self.assertEqual(durable_stock.stock_in_use(120.0, 80.0, True), 120.0)

    def test_a_good_the_household_has_no_use_for_is_all_store(self):
        self.assertEqual(durable_stock.stock_in_use(0.0, 500.0, True), 0.0)


class Rules(unittest.TestCase):
    def test_the_two_answers(self):
        self.assertFalse(durable_stock.sold_when_spare())
        self.assertTrue(durable_stock.kept_while_used())
        self.assertIs(rule_sets.RULE_SETS["search"].durables_kept_while_used, durable_stock.sold_when_spare)
        self.assertIs(rule_sets.RULE_SETS["clearing"].durables_kept_while_used, durable_stock.kept_while_used)


if __name__ == "__main__":
    unittest.main()
