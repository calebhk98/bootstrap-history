"""Complaint 345: a concern whose data states its lines' hours is crewed by those hours over a person-year, whatever its
takings. Rule: business_crew_rule.hands and staff_by_trade on built crew figures. The firm count that follows the
market is a measure of the whole economy (Complaint 473)."""
QUICK_TOPIC = True

import unittest

from sim.agents.api import business_crew_rule
from sim.agents.business_crew_rule import CrewFigures

HOURS_PER_PERSON_YEAR = 2000.0
HOURS_BY_TRADE = {"smith": 3000.0, "labourer": 1000.0}


def derived_plant(revenue):
	return CrewFigures(
		scholars_figure=0.0, artisans_figure=0.0, revenue=revenue, upkeep=100.0, hours_per_person_year=HOURS_PER_PERSON_YEAR,
		supervision_share=0.25, hands_per_revenue=lambda: 300.0, foreman_share=0.25, unskilled_trade=lambda: "labourer",
		revenue_basis="output", hours_by_trade=HOURS_BY_TRADE)


def crew_people(plant):
	scholars = business_crew_rule.hands(plant, lambda: False)[0]
	return sum(business_crew_rule.staff_by_trade(plant, scholars).values())


class DerivedConcernCrewTests(unittest.TestCase):
	def test_the_crew_is_the_plants_hours_over_a_person_year(self):
		self.assertAlmostEqual(crew_people(derived_plant(900.0)), sum(HOURS_BY_TRADE.values()) / HOURS_PER_PERSON_YEAR)

	def test_the_crew_does_not_move_with_the_takings(self):
		self.assertEqual(crew_people(derived_plant(900.0)), crew_people(derived_plant(2700.0)))


if __name__ == "__main__":
	unittest.main()
