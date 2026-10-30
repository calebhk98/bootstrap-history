"""The ledger's plain rules: a stock change lands once in the stock and once in the year's opening snapshot
(Complaint 681). Each test calls one function of sim/ledger/rules.py."""

QUICK_TOPIC = True

import collections
import unittest

from sim.ledger.api import rules


class AddTonnesTests(unittest.TestCase):
	def test_tonnes_land_once_in_the_stock_and_once_in_the_opening_snapshot(self):
		stock, opening = collections.Counter({"iron": 2.0}), {"iron": 2.0}
		rules.add_tonnes(stock, opening, "iron", 3.0)
		self.assertEqual((stock["iron"], opening["iron"]), (5.0, 5.0))

	def test_a_commodity_new_to_the_snapshot_starts_from_nothing(self):
		stock, opening = collections.Counter(), {}
		rules.add_tonnes(stock, opening, "goat", -1.5)
		self.assertEqual((stock["goat"], opening["goat"]), (-1.5, -1.5))


if __name__ == "__main__":
	unittest.main()
