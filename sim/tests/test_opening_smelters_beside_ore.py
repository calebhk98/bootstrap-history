"""Complaint 473: the opening puts each processor of a fixed-site good beside that good's supply, in a market area that
makes it. Reads the Rome opening the harness game saved; no data is named in the engine."""
import math
import unittest

from sim.economy import api as economy_api
from sim.economy import location_inputs, sites
from sim.engine.economy_port_setup import build_setup
from sim.tests import harness

FAR_CARRIAGE_SHARE_OF_ORE_VALUE = 0.5     # a smelter farther than this share of its ore's value per kg from the ore is not beside it


class OpeningSmeltersBesideOreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        game = harness.sim()
        cls.setup = build_setup(game, game.state.economy.agent_economy["opening"])
        cls.economy = economy_api.blank_economy(cls.setup)
        by_limits = sites.limits_by_recipe(cls.setup.site_limits)
        cls.fixed = {}
        for recipe_id, recipe in cls.setup.recipes.items():
            incumbents = {good: other for other, each in cls.setup.recipes.items() if sites.is_sited(each, by_limits)
                          for good in each.outputs}
            fixed = location_inputs.fixed_inputs(recipe, incumbents, cls.setup.recipes, by_limits)
            if fixed and not sites.is_sited(recipe, by_limits):
                cls.fixed[recipe_id] = fixed

    def test_a_processor_of_a_fixed_site_good_sits_in_a_market_area_that_makes_it(self):
        record, area_map = self.economy.record, self.economy.area_map
        self.assertTrue(self.fixed)
        for recipe_id, fixed in self.fixed.items():
            for good in fixed:
                supplied = {area_map.area_of(good, producer.tile) for producer in record.producers.values()
                            if good in self.setup.recipes[producer.recipe_id].outputs}
                for producer in record.producers.values():
                    if producer.recipe_id == recipe_id:
                        self.assertIn(area_map.area_of(good, producer.tile), supplied, "%s at %s" % (recipe_id, producer.tile))

    def test_a_smelter_sits_at_or_next_to_its_ore(self):
        record, carriage = self.economy.record, self.economy.carriage
        for recipe_id, fixed in self.fixed.items():
            for good in fixed:
                sources = {producer.tile for producer in record.producers.values()
                           if good in self.setup.recipes[producer.recipe_id].outputs}
                price_per_tonne = self.setup.opening_prices[good] * 1000.0 / self.setup.specs[good].unit_mass_kg
                for producer in record.producers.values():
                    if producer.recipe_id == recipe_id:
                        nearest = min(carriage.cost_per_tonne(source, producer.tile) for source in sources)
                        self.assertTrue(math.isfinite(nearest))
                        self.assertLessEqual(nearest, FAR_CARRIAGE_SHARE_OF_ORE_VALUE * price_per_tonne,
                                             "%s at %s is %.0f a tonne from %s" % (recipe_id, producer.tile, nearest, good))


if __name__ == "__main__":
    unittest.main()
