"""The opening sizes crop producers at their tile's yield factor, and the runs it asks for make every good in the quantity
demanded, inputs included. Each rule is called on figures written out here: `opening._add_producers` places a producer at its
tile's yield, `opening_runs.mean_yields` turns the tiles' yields into the factor runs are sized at, and
`opening_runs.required_runs` sizes the runs; no economy is opened."""
import types
import unittest
from unittest import mock

from sim.economy import opening, opening_runs
from sim.economy.setup import recipe_tile_key
from sim.tests import economy_fixture as fixture

QUICK_TOPIC = True

TOLERANCE = 1e-6      # share of the demand the float sums may miss by
YIELD_BY_TILE = {fixture.TOWN: 0.5, fixture.FARMS: 0.8, fixture.HILLS: 0.4}
PEOPLE = {fixture.TOWN: 100.0, fixture.FARMS: 200.0, fixture.HILLS: 50.0}


def yields_keyed(factor_scale=1.0):
    return {recipe_tile_key(fixture.FARM, tile): factor * factor_scale for tile, factor in YIELD_BY_TILE.items()}


def setup_with(yield_factor_by_recipe_tile):
    return types.SimpleNamespace(
        recipes=fixture.recipes(), opening_prices={fixture.GRAIN: 100.0}, opening_wages={fixture.LABOURER: 1.0},
        yield_factor_by_recipe_tile=yield_factor_by_recipe_tile, opening_population_by_tile=dict(PEOPLE),
        tiles={tile: None for tile in PEOPLE}, recipe_allowed=lambda recipe_id, tile: True)


class OpeningCropsAtTileYieldTests(unittest.TestCase):
    def test_crop_producers_carry_their_tiles_yield(self):
        setup = setup_with(yields_keyed())
        record = types.SimpleNamespace(producers={}, cohorts={tile: types.SimpleNamespace(tile=tile) for tile in PEOPLE})
        with mock.patch.object(opening, "_richest_class", return_value=0):
            opening._add_producers(setup, record, setup.recipes[fixture.FARM], {tile: 10.0 for tile in PEOPLE}, {}, {})
        self.assertEqual({producer.tile: producer.yield_factor for producer in record.producers.values()}, YIELD_BY_TILE)

    def test_a_lower_yield_takes_more_runs_to_make_the_same_grain(self):
        recipes = fixture.recipes()
        better = opening_runs.mean_yields(setup_with(yields_keyed()), recipes)[fixture.FARM]
        poorer = opening_runs.mean_yields(setup_with(yields_keyed(0.5)), recipes)[fixture.FARM]
        self.assertAlmostEqual(poorer, 0.5 * better)
        demand = {fixture.TOWN: {fixture.GRAIN: 5000.0}}
        ranked = {fixture.GRAIN: [fixture.FARM]}
        runs = lambda yield_factor: opening_runs.required_runs(demand, ranked, recipes, None, {fixture.FARM: yield_factor})[fixture.FARM]
        self.assertGreater(runs(poorer), runs(better))


class RunsMeetDemandTests(unittest.TestCase):
    def test_crop_goods_are_made_in_the_quantity_demanded_at_the_yield_runs_are_sized_at(self):
        recipes = fixture.recipes()
        yield_factor = 0.6
        runs = opening_runs.required_runs({fixture.TOWN: {fixture.GRAIN: 5000.0}}, {fixture.GRAIN: [fixture.FARM]}, recipes,
                                          None, {fixture.FARM: yield_factor})
        made = runs[fixture.FARM] * recipes[fixture.FARM].outputs[fixture.GRAIN] * yield_factor
        self.assertGreaterEqual(made, 5000.0 * (1.0 - TOLERANCE))

    def test_every_input_is_made_in_the_quantity_the_runs_that_take_it_need(self):
        recipes = fixture.recipes()
        ranked = {fixture.METAL: [fixture.SMELT], fixture.ORE: [fixture.MINE]}
        runs = opening_runs.required_runs({fixture.TOWN: {fixture.METAL: 7.0}}, ranked, recipes)
        taken = runs[fixture.SMELT] * recipes[fixture.SMELT].inputs[fixture.ORE]
        made = runs[fixture.MINE] * recipes[fixture.MINE].outputs[fixture.ORE]
        self.assertGreater(taken, 0.0)
        self.assertGreaterEqual(made, taken * (1.0 - TOLERANCE))


if __name__ == "__main__":
    unittest.main()
