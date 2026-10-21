"""Complaint 657: a higher rate on what actors earn makes them keep more of it off the rolls, and the more of the
payers the state's officials reach, the less. Each test builds the inputs and calls the rule."""
import unittest
from types import SimpleNamespace

from sim.agents import evasion, fiscal_response, revenue
from sim.agents.revenue_bases import Base
from sim.agents.tuning_evasion import HIDEABLE_SHARE_OF_INCOME

QUICK_TOPIC = True


def payer(money=1.0e9):
	return SimpleNamespace(record=SimpleNamespace(stratum="labourer"), money=money)


def income_form(rate):
	return {"form": "income_levy", "basis": "stratum_income", "rate": rate}


def assessed(rate, collectible, incomes=(1000.0, 3000.0), money=1.0e9):
	payers = tuple((payer(money), income) for income in incomes)
	return revenue.taxed_actors(income_form(rate), Base(sum(incomes), payers=payers), collectible)


class HiddenShareTests(unittest.TestCase):
	def test_a_higher_rate_hides_more(self):
		shares = [evasion.hidden_share(rate, 0.5) for rate in (0.02, 0.05, 0.1, 0.2)]
		self.assertEqual(shares, sorted(shares))
		self.assertGreater(shares[-1], shares[0])

	def test_officials_reaching_more_payers_leave_less_hidden(self):
		shares = [evasion.hidden_share(0.1, reach) for reach in (0.2, 0.4, 0.6, 0.8)]
		self.assertEqual(shares, sorted(shares, reverse=True))
		self.assertGreater(shares[0], shares[-1])

	def test_nothing_is_hidden_from_a_state_that_reaches_everyone_or_where_no_tax_is_laid(self):
		self.assertEqual(evasion.hidden_share(0.1, 1.0), 0.0)
		self.assertEqual(evasion.hidden_share(0.0, 0.3), 0.0)

	def test_no_more_than_can_be_hidden_at_all(self):
		self.assertEqual(evasion.hidden_share(1.0, 0.1), HIDEABLE_SHARE_OF_INCOME)

	def test_a_rate_raise_yields_less_than_proportionally_once_hiding_grows(self):
		low, high = evasion.yield_of_rate(1000.0, 0.1, 0.4), evasion.yield_of_rate(1000.0, 0.2, 0.4)
		self.assertGreater(high, low)
		self.assertLess(high, 2.0 * low)


class AssessmentOfPayersTests(unittest.TestCase):
	def test_hidden_income_is_off_the_base_and_the_tax(self):
		result = assessed(0.1, 0.5)
		self.assertGreater(result.concealed, 0.0)
		self.assertAlmostEqual(result.base + result.concealed, 4000.0)
		self.assertAlmostEqual(result.money, 0.5 * 0.1 * result.base)
		self.assertAlmostEqual(sum(amount for _payer, amount in result.payers), result.money)

	def test_a_higher_rate_conceals_a_larger_share_of_the_same_income(self):
		low, high = assessed(0.05, 0.5), assessed(0.2, 0.5)
		self.assertGreater(high.concealed / 4000.0, low.concealed / 4000.0)

	def test_full_reach_conceals_nothing(self):
		result = assessed(0.1, 1.0)
		self.assertEqual(result.concealed, 0.0)
		self.assertAlmostEqual(result.money, 0.1 * 4000.0)

	def test_a_payer_pays_no_more_than_its_purse_holds(self):
		result = assessed(0.1, 0.5, money=5.0)
		self.assertTrue(all(amount <= 0.5 * 5.0 + 1e-9 for _payer, amount in result.payers))


class RateRaiseMenuTests(unittest.TestCase):
	def world(self, reach):
		now = assessed(0.1, reach)
		return SimpleNamespace(revenue_assessments=lambda: [now])

	def test_the_menu_counts_the_base_a_raise_drives_into_hiding(self):
		hiding_world, open_world = self.world(0.4), self.world(1.0)
		raised = fiscal_response.rate_raise_yield(hiding_world)
		naive = 0.4 * (fiscal_response.new_rate_of(0.1) - 0.1) * hiding_world.revenue_assessments()[0].base
		self.assertGreater(raised, 0.0)
		self.assertLess(raised, naive)
		self.assertAlmostEqual(fiscal_response.rate_raise_yield(open_world),
							   (fiscal_response.new_rate_of(0.1) - 0.1) * 4000.0)

	def test_a_form_on_a_base_nobody_hides_yields_the_extra_rate_on_the_base(self):
		plain = revenue.Assessment("wealth", "coin_stock", 20000.0, 0.01, 200.0, collectible=1.0)
		world = SimpleNamespace(revenue_assessments=lambda: [plain])
		self.assertAlmostEqual(fiscal_response.rate_raise_yield(world), 20000.0 * 0.01 * fiscal_response.RATE_RAISE_STEP)


if __name__ == "__main__":
	unittest.main()
