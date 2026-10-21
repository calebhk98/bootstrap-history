"""A business's crew is the trades its plant's recipe names, for the founder and for a firm alike, on built crew figures.
The same over every plant of a real game is in test_crew_is_the_recipes_trades_scenario.py."""
QUICK_TOPIC = True

import unittest

from sim.agents.api import business_crew_rule
from sim.agents.business_crew_rule import CrewFigures
from sim.world import plant_figures

HOURS_PER_PERSON_YEAR = 2000.0


def tannery(**changes):
	base = dict(scholars_figure=0.0, artisans_figure=0.0, revenue=900.0, upkeep=100.0,
				hours_per_person_year=HOURS_PER_PERSON_YEAR, supervision_share=0.25, hands_per_revenue=lambda: 300.0,
				foreman_share=0.25, unskilled_trade=lambda: "labourer", revenue_basis="output",
				hours_by_trade={"tanner": 4000.0, "leatherworker": 2000.0, "idle": 0.0})
	base.update(changes)
	return CrewFigures(**base)


class CrewIsTheRecipesTrades(unittest.TestCase):
	def test_crew_by_trade_is_hours_over_a_person_year(self):
		crew = plant_figures.crew_by_trade({"tanner": 4000.0, "leatherworker": 2000.0, "idle": 0.0}, 2000.0)
		self.assertEqual(crew, {"tanner": 2.0, "leatherworker": 1.0})

	def test_a_plant_with_recipe_hours_hires_exactly_those_trades_and_no_generic_artisans(self):
		staff = business_crew_rule.staff_by_trade(tannery(), scholars=0.0)
		self.assertEqual(staff, {"tanner": 2.0, "leatherworker": 1.0})
		self.assertNotIn("artisan", staff)
		self.assertNotIn("labourer", staff)

	def test_a_plant_whose_data_states_no_hours_falls_back_to_the_unskilled_trade(self):
		staff = business_crew_rule.staff_by_trade(tannery(revenue_basis=None, hours_by_trade=None), scholars=0.0)
		self.assertEqual(set(staff), {"labourer"})

	def test_founder_and_firm_hold_the_same_number_of_people(self):
		for plant in (tannery(), tannery(revenue_basis=None, hours_by_trade=None), tannery(stated_people=5.0, revenue_basis=None)):
			_scholars, craftsmen = business_crew_rule.founder_staffed_hands(plant)
			self.assertAlmostEqual(craftsmen, sum(business_crew_rule.crew_by_trade(plant).values()), places=9)


if __name__ == "__main__":
	unittest.main()
