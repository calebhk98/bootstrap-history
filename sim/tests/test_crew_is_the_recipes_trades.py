"""A business's crew is the trades its plant's recipe names, for the founder and for a firm alike."""
import unittest

from .harness import sim

from sim.engine.agents_port import SimWorld
from sim.world import plant_figures


class CrewIsTheRecipesTrades(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.game = sim(capital=1e9)
		cls.world = SimWorld(cls.game)
		cls.derived = {node_id: node for node_id, node in sorted(cls.game.nodes.items())
					   if plant_figures.derived_crew_hours(node.get("_revenue_basis"), node.get("_labour_hours_per_year")) > 0.0}

	def test_crew_by_trade_is_hours_over_a_person_year(self):
		crew = plant_figures.crew_by_trade({"tanner": 4000.0, "leatherworker": 2000.0, "idle": 0.0}, 2000.0)
		self.assertEqual(crew, {"tanner": 2.0, "leatherworker": 1.0})

	def test_a_plant_with_recipe_hours_hires_exactly_those_trades(self):
		self.assertTrue(self.derived)
		for node_id, node in self.derived.items():
			named = {trade for trade, hours in node["_labour_hours_per_year"].items() if hours > 0.0}
			self.assertTrue(named <= set(self.world.concern_staff(node_id)), node_id)

	def test_a_tanning_plant_hires_tanners_and_no_generic_artisans(self):
		node_id = next(node_id for node_id, node in self.derived.items()
					   if node["_labour_hours_per_year"].get("tanner", 0.0) > 0.0)
		crew = self.world.concern_staff(node_id)
		self.assertGreater(crew.get("tanner", 0.0), 0.0)
		self.assertNotIn("artisan", crew)

	def test_founder_and_firm_hold_the_same_number_of_people(self):
		for node_id in self.derived:
			_scholars, craftsmen = self.game.venture_hands_founder_staffed(node_id)
			self.assertAlmostEqual(craftsmen, sum(self.game.venture_crew_by_trade(node_id).values()), places=9, msg=node_id)


if __name__ == "__main__":
	unittest.main()
