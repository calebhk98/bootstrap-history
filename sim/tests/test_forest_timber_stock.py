"""Complaint 539: forests are a stock of standing timber that felling draws down and growth restores, and
the firms that fell wood are limited to, and made dearer by, the stock of the tile they work."""
QUICK_TOPIC = True

import types
import unittest

from sim.markets import port_timber
from sim.geography import api as geography
from sim.geography import forest_timber
from sim.resources.api import FellTimber, RegrowTimber
from sim.resources.state import ResourcesWorld
from sim.tests import resources_stand_in
from sim.world import demand

FIREWOOD = "firewood_kg"
OUTPUTS = {FIREWOOD: {FIREWOOD: 1000.0}, "bread_kg": {"bread_kg": 5.0}}
WORLD_MAP = geography.open_map()


def _host(felled=None):
    """A game for the port's timber hooks: the resources module holds the felled ledger and applies the commands."""
    module = resources_stand_in.build(world=ResourcesWorld(forest_felled=dict(felled or {})))
    handlers = {FellTimber: module.fell_timber, RegrowTimber: module.regrow_timber}
    return types.SimpleNamespace(world_map=WORLD_MAP, module=module, timber_felled=module.timber_felled,
                                 send=lambda command: handlers[type(command)](command))


def _forest_tile():
    return max(geography.tile_ids(WORLD_MAP), key=lambda tile: forest_timber.full_tonnes(WORLD_MAP, tile))


def _bare_tile():
    return next(tile for tile in geography.tile_ids(WORLD_MAP) if forest_timber.full_tonnes(WORLD_MAP, tile) == 0.0)


def _limit(host, tile):
    found = [limit for limit in port_timber.limits(host, OUTPUTS, [tile]) if limit.tile == tile]
    return found[0] if found else None


class StockTests(unittest.TestCase):

    def test_firewood_is_a_timber_recipe_and_other_goods_are_not(self):
        self.assertEqual(set(port_timber.timber_recipes(OUTPUTS)), {FIREWOOD})

    def test_felling_lowers_the_standing_stock_and_never_below_nothing(self):
        tile = _forest_tile()
        full = forest_timber.full_tonnes(WORLD_MAP, tile)
        felled = geography.fell_timber({}, tile, full / 4.0, WORLD_MAP)
        self.assertAlmostEqual(geography.standing_timber_tonnes(felled, tile, WORLD_MAP), full * 0.75)
        felled = geography.fell_timber(felled, tile, full * 10.0, WORLD_MAP)
        self.assertEqual(geography.standing_timber_tonnes(felled, tile, WORLD_MAP), 0.0)

    def test_the_cost_of_a_tonne_rises_and_the_room_falls_as_the_stock_runs_down(self):
        tile = _forest_tile()
        full = forest_timber.full_tonnes(WORLD_MAP, tile)
        hours = sum(demand.production_data()[FIREWOOD]["labour_hours"].values())
        cost, room = [], []
        for share in (0.0, 0.3, 0.6, 0.9):
            limit = _limit(_host({tile: full * share}), tile)
            cost.append(hours / limit.yield_factor)
            room.append(limit.capacity_runs_per_year)
        self.assertEqual(cost, sorted(cost))
        self.assertLess(cost[0], cost[-1])
        self.assertEqual(room, sorted(room, reverse=True))

    def test_a_worked_out_tile_has_no_limit_and_a_tile_without_forest_never_had_one(self):
        tile = _forest_tile()
        full = forest_timber.full_tonnes(WORLD_MAP, tile)
        self.assertIsNone(_limit(_host({tile: full}), tile))
        self.assertIsNone(_limit(_host(), _bare_tile()))

    def test_regrowth_restores_the_stock_at_the_increment_of_the_tiles_forest(self):
        tile = _forest_tile()
        full = forest_timber.full_tonnes(WORLD_MAP, tile)
        per_year = (forest_timber.forest_hectares(WORLD_MAP, tile)
                    * geography.timber_increment_tonnes_per_hectare_year(tile, WORLD_MAP))
        self.assertGreater(per_year, 0.0)
        felled = {tile: full / 2.0}
        after = geography.regrow_timber(felled, WORLD_MAP)
        self.assertAlmostEqual(felled[tile] - after[tile], per_year, delta=per_year * 1e-9)
        years = 0
        while felled and years < 10000:
            felled = geography.regrow_timber(felled, WORLD_MAP)
            years += 1
        self.assertEqual(felled, {})
        self.assertAlmostEqual(years, full / 2.0 / per_year, delta=1.0)

    def test_what_firms_fell_is_drawn_from_the_tile_and_the_stock_regrows_a_year(self):
        tile = _forest_tile()
        host = _host()
        full = forest_timber.full_tonnes(WORLD_MAP, tile)
        runs = full / 4.0
        port_timber.fell(host, {(FIREWOOD, tile): runs}, OUTPUTS)
        self.assertAlmostEqual(host.module.world.forest_felled[tile], runs)
        port_timber.regrow(host)
        self.assertLess(host.module.world.forest_felled[tile], runs)

    def test_the_haul_to_standing_wood_lengthens_as_more_is_cut(self):
        tile = _forest_tile()
        full = forest_timber.full_tonnes(WORLD_MAP, tile)
        near = geography.timber_haul_km({tile: full * 0.1}, tile, WORLD_MAP)
        far = geography.timber_haul_km({tile: full * 0.6}, tile, WORLD_MAP)
        self.assertEqual(geography.timber_haul_km({}, tile, WORLD_MAP), 0.0)
        self.assertLess(near, far)


if __name__ == "__main__":
    unittest.main()
