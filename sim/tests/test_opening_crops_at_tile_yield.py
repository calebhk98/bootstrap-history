"""Complaint 537: the opening sizes crop producers at their tile's yield factor, so what they make in a year is what the
opening demands (final demand and the inputs of the producers sized beside them), and the year-one yields agree."""
import unittest

from sim.economy import opening, opening_runs
from sim.economy.setup import recipe_tile_key
from sim.engine.economy_port_setup import build_setup
from sim.tests import harness
from sim.tests.test_opening_inputs_have_suppliers import flows

TOLERANCE = 1e-6


class OpeningCropsAtTileYieldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.setup = build_setup(harness.unopened_sim(civ="rome_100ad"))
        cls.record, _areas, _carriage = opening.open_economy(cls.setup)
        cls.crops = sorted({key.partition("@")[0] for key in cls.setup.yield_factor_by_recipe_tile})

    def test_crop_producers_carry_their_tiles_yield(self):
        crop_producers = [producer for producer in self.record.producers.values() if producer.recipe_id in self.crops]
        self.assertTrue(crop_producers)
        for producer in crop_producers:
            factor = self.setup.yield_factor_by_recipe_tile[recipe_tile_key(producer.recipe_id, producer.tile)]
            self.assertGreater(factor, 0.0)
            self.assertEqual(producer.yield_factor, factor)

    def test_crop_goods_are_made_in_the_quantity_the_opening_demands(self):
        made, taken = flows(self.setup, self.record)
        basket = self.record.opening_basket
        short = {}
        for recipe_id in self.crops:
            for good in self.setup.recipes[recipe_id].outputs:
                wanted = basket.get(good, 0.0) + taken.get(good, 0.0)
                if made.get(good, 0.0) < wanted * (1.0 - TOLERANCE):
                    short[good] = (made.get(good, 0.0), wanted)
        self.assertEqual(short, {})

    def test_a_run_counted_at_a_lower_yield_takes_more_runs(self):
        recipe_id = next(each for each in self.crops if self.setup.recipes[each].outputs)
        recipe = self.setup.recipes[recipe_id]
        good = next(iter(recipe.outputs))
        demand = {"town": {good: 1000.0}}
        full = opening_runs.required_runs(demand, {good: [recipe_id]}, {recipe_id: recipe})
        half = opening_runs.required_runs(demand, {good: [recipe_id]}, {recipe_id: recipe}, None, {recipe_id: 0.5})
        self.assertAlmostEqual(half[recipe_id], 2.0 * full[recipe_id], delta=1e-9 * full[recipe_id])


if __name__ == "__main__":
    unittest.main()
