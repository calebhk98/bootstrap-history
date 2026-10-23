"""Complaint 438: a failure cannot take the purse past the credit limit; the part the purse and the credit line cannot bear
is billed to the project to redo. `CreditMixin.bearable_part_of` is called on a stub household whose credit limit reads
the capital left (a status term shrinks as positive capital goes). The failure charge, a failed bounty and the coin guard are in `test_failure_charge_rules`; selling stock at the market's limits
is in `test_sale_price_climb` and `test_complaint_578_sell_stock_left`.
"""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.engine.economy_credit import CreditMixin

BASE_LIMIT = 500.0
STATUS_SHARE = 0.2


class StubHousehold:
	"""A purse and a credit line that is the base plus a share of positive capital."""

	def __init__(self, capital):
		self.state = SimpleNamespace(household=SimpleNamespace(capital=capital))

	def credit_limit(self, _capital=None):
		held = self.state.household.capital if _capital is None else _capital
		return BASE_LIMIT + STATUS_SHARE * max(0.0, held)

	bearable_part_of = CreditMixin.bearable_part_of


class BearablePartTests(unittest.TestCase):
	def test_a_loss_inside_the_purse_is_borne_whole(self):
		self.assertEqual(StubHousehold(1000.0).bearable_part_of(300.0), 300.0)

	def test_a_loss_inside_the_purse_and_the_credit_line_is_borne_whole(self):
		self.assertEqual(StubHousehold(100.0).bearable_part_of(400.0), 400.0)

	def test_a_loss_past_the_credit_line_is_borne_only_to_the_line(self):
		household = StubHousehold(100.0)
		loss = 5000.0
		borne = household.bearable_part_of(loss)
		self.assertLess(borne, loss)
		capital_after = household.state.household.capital - borne
		self.assertGreaterEqual(capital_after, -household.credit_limit(_capital=household.state.household.capital - loss) - 1e-9)

	def test_the_part_not_borne_is_the_rest_of_the_loss(self):
		household = StubHousehold(-200.0)
		loss = 1000.0
		borne = household.bearable_part_of(loss)
		self.assertAlmostEqual(borne + (loss - borne), loss)
		self.assertGreaterEqual(borne, 0.0)

	def test_a_purse_already_at_the_limit_bears_nothing(self):
		household = StubHousehold(-BASE_LIMIT)
		self.assertEqual(household.bearable_part_of(100.0), 0.0)

	def test_a_purse_past_the_limit_bears_nothing_and_never_a_negative_amount(self):
		self.assertEqual(StubHousehold(-BASE_LIMIT - 50.0).bearable_part_of(100.0), 0.0)

	def test_nothing_lost_nothing_borne(self):
		self.assertEqual(StubHousehold(100.0).bearable_part_of(0.0), 0.0)


if __name__ == "__main__":
	unittest.main()
