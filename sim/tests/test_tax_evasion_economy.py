"""Complaint 657: the economy's money and harvest forms use the same hiding rule as the actor layer, handed in by the
port. Each test builds the inputs and calls `taxes.assess`."""
import unittest

from sim.agents import evasion
from sim.economy.taxes import TaxForm, YearFacts, assess

QUICK_TOPIC = True

STATE = "state"
DUTY = TaxForm("import_duty", "imports_value", 0.1)
TITHE = TaxForm("tithe", "harvest", 0.1, "grain")


def facts():
	return YearFacts(currency="coin", imports_paid={("trader", "silk"): 1000.0}, cash={"trader": 1.0e9},
					 output={("farm", "grain"): 1000.0}, producer_tile={"farm": "t1"})


def collected(form, reach, hiding):
	_transfers, _moves, assessments = assess([form], facts(), STATE, {"grain": 1.0}, reach, hiding)
	return assessments[0]


class MoneyFormHidingTests(unittest.TestCase):
	def test_without_a_hiding_rule_only_the_officials_reach_limits_collection(self):
		result = collected(DUTY, 0.5, None)
		self.assertAlmostEqual(result.collected_value, 0.5 * 0.1 * 1000.0)
		self.assertEqual(result.concealed_value, 0.0)

	def test_hidden_income_is_neither_collected_nor_counted_as_unreached(self):
		result = collected(DUTY, 0.5, evasion.hidden_share)
		hidden = evasion.hidden_share(0.1, 0.5)
		self.assertGreater(hidden, 0.0)
		self.assertAlmostEqual(result.collected_value, 0.5 * 0.1 * 1000.0 * (1.0 - hidden))
		self.assertAlmostEqual(result.concealed_value, 0.1 * 1000.0 * hidden)
		self.assertAlmostEqual(result.collected_value + result.evaded_value + result.concealed_value, 0.1 * 1000.0)

	def test_the_economy_collects_what_the_actor_layer_would_declare(self):
		reach, rate = 0.4, 0.1
		result = collected(DUTY, reach, evasion.hidden_share)
		self.assertAlmostEqual(result.collected_value, evasion.yield_of_rate(1000.0, rate, reach))

	def test_a_higher_rate_hides_a_larger_share(self):
		low = collected(TaxForm("duty", "imports_value", 0.05), 0.5, evasion.hidden_share)
		high = collected(TaxForm("duty", "imports_value", 0.2), 0.5, evasion.hidden_share)
		self.assertGreater(high.concealed_value / 0.2, low.concealed_value / 0.05)

	def test_officials_reaching_every_payer_leave_nothing_hidden(self):
		result = collected(DUTY, 1.0, evasion.hidden_share)
		self.assertEqual(result.concealed_value, 0.0)
		self.assertAlmostEqual(result.collected_value, 100.0)


class HarvestFormHidingTests(unittest.TestCase):
	def test_a_grower_keeps_hidden_grain_off_the_levy(self):
		_transfers, moves, assessments = assess([TITHE], facts(), STATE, {"grain": 1.0}, 0.5, evasion.hidden_share)
		hidden = evasion.hidden_share(0.1, 0.5)
		self.assertGreater(hidden, 0.0)
		self.assertAlmostEqual(sum(move.quantity for move in moves), 0.5 * 0.1 * 1000.0 * (1.0 - hidden))
		self.assertAlmostEqual(assessments[0].concealed_value, 0.1 * 1000.0 * hidden)

	def test_a_rate_that_is_raised_collects_less_than_proportionally(self):
		def grain(rate):
			form = TaxForm("tithe", "harvest", rate, "grain")
			return collected(form, 0.4, evasion.hidden_share).collected_quantity
		self.assertLess(grain(0.2), 2.0 * grain(0.1))


if __name__ == "__main__":
	unittest.main()
