"""Complaint 660: the guard staff per head the state's sizing rule gives Rome's opening state, set against the sourced
staff-per-head anchors (Complaints/reports/research-tax-response-and-state-staff.md, 2.1). The rule is called on the
opening's inputs; no game is built."""
import json
import os
import unittest

from sim.agents import order
from sim.agents.revenue_labour import HOURS_PER_WORKING_DAY
from sim.unit_conversions import HOURS_PER_PERSON_YEAR

QUICK_TOPIC = True

# Pelcer, review of Homoth-Kuhs, Phylakes und Phylakon-Steuer (sehepunkte 7, 2007, Nr. 10): "1 archephodos and 4 phylakes on
# 300 inhabitants"; villages "from 1:50 to 1:130"; P. Oxy. I 43 verso: 60 phylakes for "36,000 inhabitants".
VILLAGE_LOW = 1.0 / 130.0
VILLAGE_HIGH = 1.0 / 50.0
NOME_CAPITAL = 60.0 / 36000.0
CAPITAL_ROME = (7 * 1000.0 + 3 * 500.0) / 1_000_000.0   # carried from research-state-staffing.md

ROME_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "civilizations", "rome_100ad.json")


def rome_guards_per_head():
	with open(ROME_FILE, encoding="utf-8") as handle:
		people = float(json.load(handle)["population"])
	working_days = HOURS_PER_PERSON_YEAR / HOURS_PER_WORKING_DAY
	return order.guards_kept(people, working_days) / people


class GuardStaffPerHead(unittest.TestCase):
	def test_the_anchors_are_the_arithmetic_of_the_sources(self):
		self.assertAlmostEqual(NOME_CAPITAL, 0.00167, places=5)
		self.assertAlmostEqual(VILLAGE_LOW, 0.00769, places=5)
		self.assertAlmostEqual(VILLAGE_HIGH, 0.02)

	def test_the_states_guards_per_head_are_under_the_densest_sourced_anchor(self):
		ratio = rome_guards_per_head()
		self.assertGreater(ratio, 0.0)
		self.assertLess(ratio, max(VILLAGE_HIGH, CAPITAL_ROME))

	@unittest.expectedFailure
	def test_the_states_guards_per_head_fall_inside_the_sourced_range(self):
		# Complaint 660 (open): the sizing rule's figure falls far below the lowest sourced density. The anchors are settled
		# places, not province-wide averages, so the lowest is a generous floor; the gap stays visible until the rule sizes
		# guards from what they did (patrols per settlement, crimes per district) rather than PATROL_DAYS_PER_PERSON.
		ratio = rome_guards_per_head()
		self.assertGreaterEqual(ratio, min(NOME_CAPITAL, VILLAGE_LOW, CAPITAL_ROME))
		self.assertLessEqual(ratio, max(VILLAGE_HIGH, CAPITAL_ROME))

if __name__ == "__main__":
	unittest.main()
