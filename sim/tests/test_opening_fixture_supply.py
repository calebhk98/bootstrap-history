"""The opening sizes crop producers at their tile's yield factor, and every input the sized producers take is made in the quantity
they take. Opened on the fixture economy through `economy_api.blank_economy`; no game, no data."""
import unittest

from sim.economy import api as economy_api
from sim.economy.setup import recipe_tile_key
from sim.tests import economy_fixture as fixture
from sim.tests.test_fit_to_supply_chain_rule import flows

QUICK_TOPIC = True

TOLERANCE = 1e-6      # share of the demand the float sums may miss by
YIELD_BY_TILE = {fixture.TOWN: 0.5, fixture.FARMS: 0.8, fixture.HILLS: 0.4}


def opened(yield_by_tile):
    setup = fixture.small_setup(yield_factor_by_recipe_tile={
        recipe_tile_key(fixture.FARM, tile): factor for tile, factor in yield_by_tile.items()})
    return setup, economy_api.blank_economy(setup).record


class OpeningCropsAtTileYieldTests(unittest.TestCase):
    def setUp(self):
        self.setup, self.record = opened(YIELD_BY_TILE)

    def test_crop_producers_carry_their_tiles_yield(self):
        crop_producers = [producer for producer in self.record.producers.values() if producer.recipe_id == fixture.FARM]
        self.assertTrue(crop_producers)
        for producer in crop_producers:
            self.assertEqual(producer.yield_factor, YIELD_BY_TILE[producer.tile])

    def test_crop_goods_are_made_in_the_quantity_the_opening_demands(self):
        made, taken = flows(self.setup, self.record)
        wanted = self.record.opening_basket.get(fixture.GRAIN, 0.0) + taken.get(fixture.GRAIN, 0.0)
        self.assertGreater(wanted, 0.0)
        self.assertGreaterEqual(made[fixture.GRAIN], wanted * (1.0 - TOLERANCE))

    def test_a_lower_yield_takes_more_runs_to_make_the_same_grain(self):
        _setup, poor = opened({tile: 0.5 * factor for tile, factor in YIELD_BY_TILE.items()})
        runs = lambda record: sum(p.expected_sales for p in record.producers.values() if p.recipe_id == fixture.FARM)
        self.assertGreater(runs(poor), runs(self.record))


class OpeningInputsHaveSuppliersTests(unittest.TestCase):
    def test_every_input_is_made_in_the_quantity_the_producers_take(self):
        setup, record = opened(YIELD_BY_TILE)
        made, taken = flows(setup, record)
        self.assertGreater(taken[fixture.ORE], 0.0)
        short = {good: (made.get(good, 0.0), wanted) for good, wanted in taken.items()
                 if made.get(good, 0.0) < wanted * (1.0 - TOLERANCE)}
        self.assertEqual(short, {})


if __name__ == "__main__":
    unittest.main()
