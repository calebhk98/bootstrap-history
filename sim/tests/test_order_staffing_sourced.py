"""Complaint 660: the guard time per person is held under the density of the capital's standing watch; the rest stay labelled."""
QUICK_TOPIC = True

import unittest

from sim.agents import order
from sim.agents.revenue_labour import HOURS_PER_WORKING_DAY
from sim.agents.tuning_order import FORESTER_DAYS_PER_PERSON, INSPECTION_DAYS_PER_PERSON, PATROL_DAYS_PER_PERSON
from sim.constants import REGISTRY

# Wikipedia 'Vigiles': "seven cohorts each 1,000 men strong"; 'Cohortes urbanae': "three urban cohorts", "around five
# hundred men" each; 'Rome': "population of the city until AD 300 was 1 million".
VIGILES = 7 * 1000.0
URBAN_COHORT_MEN = 3 * 500.0
ROME_PEOPLE = 1_000_000.0
HOURS_PER_PERSON_YEAR = 2000.0


def capital_watch_days_per_person(working_days):
	"""Guard-days per person per year of the capital's standing watch, counting each man for a working year."""
	return (VIGILES + URBAN_COHORT_MEN) / ROME_PEOPLE * working_days


class OrderStaffing(unittest.TestCase):

	def test_the_capital_watch_density_is_the_arithmetic_of_the_sources(self):
		working_days = HOURS_PER_PERSON_YEAR / HOURS_PER_WORKING_DAY
		self.assertAlmostEqual(capital_watch_days_per_person(working_days), 1.7)

	def test_guard_time_per_person_is_under_the_capitals_density(self):
		working_days = HOURS_PER_PERSON_YEAR / HOURS_PER_WORKING_DAY
		self.assertLess(PATROL_DAYS_PER_PERSON, capital_watch_days_per_person(working_days))
		people = ROME_PEOPLE
		self.assertLess(order.guards_kept(people, working_days), VIGILES + URBAN_COHORT_MEN)

	def test_inspectors_and_foresters_have_no_source_and_name_their_retirement(self):
		for name, value in (("INSPECTION_DAYS_PER_PERSON", INSPECTION_DAYS_PER_PERSON),
							("FORESTER_DAYS_PER_PERSON", FORESTER_DAYS_PER_PERSON)):
			entry = REGISTRY[name]
			self.assertEqual((entry["kind"], entry["value"], entry["source"]), ("temporary_heuristic", value, None))
			self.assertIn("Complaint 660", entry["retire"])


if __name__ == "__main__":
	unittest.main()
