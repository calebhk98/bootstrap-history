"""The one crew rule and the one takings product, tested on built inputs (stage 1 of the 514 plan, rules shared by
the founder's ventures and every actor's plants)."""

QUICK_TOPIC = True

import unittest

from sim.agents.api import business_books, business_crew_rule
from sim.agents.business_crew_rule import CrewFigures

HOURS = 2000.0


def figures(**changes):
	base = dict(scholars_figure=4.0, artisans_figure=12.0, revenue=900.0, upkeep=100.0, hours_per_person_year=HOURS,
				supervision_share=0.25, hands_per_revenue=lambda: 300.0, foreman_share=0.25,
				unskilled_trade=lambda: "labourer")
	base.update(changes)
	return CrewFigures(**base)


class CrewRuleTests(unittest.TestCase):
	def test_a_plant_that_states_hours_needs_those_hours_over_a_person_year(self):
		plant = figures(revenue_basis="output", hours_by_trade={"smith": 3000.0, "labourer": 1000.0})
		scholars, craftsmen = business_crew_rule.founder_staffed_hands(plant)
		self.assertAlmostEqual(craftsmen, 4000.0 / HOURS)
		self.assertAlmostEqual(scholars, 4.0 * 0.25)
		self.assertEqual(business_crew_rule.crew_by_trade(plant), {"labourer": 0.5, "smith": 1.5})

	def test_a_plant_with_no_stated_hours_falls_back_to_supervision_or_revenue(self):
		self.assertAlmostEqual(business_crew_rule.founder_staffed_hands(figures())[1], 12.0 * 0.25)
		self.assertAlmostEqual(business_crew_rule.founder_staffed_hands(figures(revenue=3000.0))[1], 10.0)
		self.assertEqual(business_crew_rule.crew_by_trade(figures(revenue=3000.0)), {"labourer": 10.0})

	def test_a_stated_crew_beats_the_fallback(self):
		self.assertEqual(business_crew_rule.founder_staffed_hands(figures(stated_people=7.0))[1], 7.0)

	def test_a_capability_institution_that_does_not_earn_its_upkeep_ties_up_nobody(self):
		school = figures(is_capability_institution=True, revenue=50.0, upkeep=100.0)
		self.assertEqual(business_crew_rule.founder_staffed_hands(school), (0.0, 0.0))
		self.assertEqual(business_crew_rule.crew_by_trade(school), {})
		self.assertEqual(business_crew_rule.foreman(school), (None, 0.0))

	def test_scholars_are_released_only_when_the_plant_runs_without_its_founder(self):
		plant = figures()
		self.assertEqual(business_crew_rule.hands(plant, lambda: False)[0], 1.0)
		self.assertEqual(business_crew_rule.hands(plant, lambda: True), (0.0, 3.0))

	def test_the_founder_question_is_not_asked_when_no_scholars_are_held(self):
		def refuse():
			raise AssertionError("asked")
		self.assertEqual(business_crew_rule.hands(figures(scholars_figure=0.0), refuse)[0], 0.0)

	def test_the_foreman_is_the_largest_skilled_trade_of_a_plant_built_with_artisans(self):
		plant = figures(build_hours_by_trade={"artisan": 10.0, "smith": 30.0, "carpenter": 20.0, "labourer": 99.0})
		self.assertEqual(business_crew_rule.foreman(plant), ("smith", 0.25))

	def test_no_foreman_without_artisans_in_the_build_or_without_takings_or_skill(self):
		self.assertEqual(business_crew_rule.foreman(figures(build_hours_by_trade={"smith": 30.0})), (None, 0.0))
		self.assertEqual(business_crew_rule.foreman(figures(build_hours_by_trade={"artisan": 5.0, "slave": 9.0})), (None, 0.0))
		self.assertEqual(business_crew_rule.foreman(figures(revenue=0.0, build_hours_by_trade={"artisan": 1.0, "smith": 3.0})),
						 (None, 0.0))

	def test_the_pool_staff_adds_scholars_foreman_and_garrison_to_the_crew(self):
		plant = figures(revenue_basis="output", hours_by_trade={"smith": 2000.0},
						build_hours_by_trade={"artisan": 1.0, "smith": 5.0}, garrison={"soldier": 2.0, "smith": 1.0})
		staff = business_crew_rule.staff_by_trade(plant, scholars=1.0)
		self.assertEqual(staff, {"scholar": 1.0, "smith": 1.0 + 0.25 + 1.0, "soldier": 2.0})

	def test_a_trade_with_no_people_is_left_out(self):
		empty = figures(scholars_figure=0.0, revenue=0.0, artisans_figure=0.0)
		self.assertEqual(business_crew_rule.staff_by_trade(empty, 0.0), {})

	def test_the_node_adapter_reads_what_the_rule_reads(self):
		node = {"sch": 4.0, "art": 12.0, "rev": 900.0, "up": 100.0, "plant_crew_people": 7.0, "lab": {"artisan": 1.0}}
		built = business_crew_rule.figures_of(node, lambda: "labourer", HOURS, 0.25, lambda: 300.0, 0.25, False, {})
		self.assertEqual(business_crew_rule.founder_staffed_hands(built), (1.0, 7.0))


class TakingsProductTests(unittest.TestCase):
	def test_takings_scale_with_size_and_with_the_goods_price(self):
		self.assertEqual(business_books.takings_of_size(100.0, 2.5, 0.8), 200.0)
		self.assertEqual(business_books.takings_of_size(100.0, 0.0, 0.8), 0.0)
		self.assertAlmostEqual(business_books.takings_of_size(100.0, 5.0, 0.8),
							   2 * business_books.takings_of_size(100.0, 2.5, 0.8))


if __name__ == "__main__":
	unittest.main()
