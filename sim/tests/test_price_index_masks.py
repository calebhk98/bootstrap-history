"""The country masks of a price-index layout (sim/economy/price_index_masks.py) against the per-market rules they replaced, on a
small area map and a layout of written-out market keys."""

QUICK_TOPIC = True

import types
import unittest

import numpy

from sim.economy.country_figures import _traded_volumes, _traded_volumes_by_market
from sim.economy.market_areas import AreaMap
from sim.economy.market_memory import KEY_SEPARATOR
from sim.economy.price_index import MarketLayout
from sim.economy.price_index_masks import areas_touching, country_price_mask, labour_area_mask
from sim.economy.types import GoodSpec

TILES = ("a", "b", "c", "d")


class Carriage:
    """Tiles a and b are one tonne-cost apart; c and d likewise; the two pairs are far apart."""
    def costs_from(self, tile):
        near = {"a": "b", "b": "a", "c": "d", "d": "c"}[tile]
        return {tile: 0.0, near: 1.0, **{other: 1000.0 for other in TILES if other not in (tile, near)}}


def area_map():
    specs = [(GoodSpec("grain", 1.0, 0.1, 0.0, "food"), 1.0), (GoodSpec("gold", 1.0, 0.0, 0.0, "metal"), 100000.0)]
    return AreaMap(TILES, Carriage(), specs, {"a": 5.0, "b": 4.0, "c": 3.0, "d": 2.0}, threshold_share=0.01)


def per_market_rule(map_of, key, tiles):
    good, area = key.split(KEY_SEPARATOR, 1)
    by_area = map_of.tile_sets(good)
    return area not in by_area or bool(by_area[area] & tiles)


class CountryPriceMask(unittest.TestCase):
    def test_every_market_is_kept_or_dropped_as_the_per_market_rule_says(self):
        map_of = area_map()
        areas = [area.area_id for good in ("grain", "gold") for area in map_of.areas(good)]
        keys = tuple(sorted({good + KEY_SEPARATOR + area for good in ("grain", "gold", "unmapped") for area in areas + ["work@a", "nowhere"]}))
        layout = MarketLayout(keys)
        for tiles in (set(), {"a"}, {"c", "d"}, {"a", "d"}, set(TILES), {"elsewhere"}):
            expected = [per_market_rule(map_of, key, tiles) for key in layout.keys_grouped]
            self.assertEqual(country_price_mask(layout, map_of.tile_table(), tiles).tolist(), expected, tiles)

    def test_the_mask_is_not_all_one_value_so_the_comparison_means_something(self):
        map_of = area_map()
        areas = [area.area_id for area in map_of.areas("grain")]
        layout = MarketLayout(tuple(sorted("grain" + KEY_SEPARATOR + area for area in areas)))
        mask = country_price_mask(layout, map_of.tile_table(), {"a"})
        self.assertTrue(mask.any() and not mask.all())

    def test_an_area_touches_the_tiles_it_holds(self):
        table = area_map().tile_table()
        touching = areas_touching(table, {"a"})
        self.assertTrue(touching.any() and not touching.all())
        self.assertEqual(len(touching), len(table.areas))


class LabourAreaMask(unittest.TestCase):
    def test_a_place_is_kept_when_its_area_is_a_labour_area_of_one_of_the_tiles(self):
        keys = ("smith|work@a", "smith|work@b", "smith|a@b0", "weaver|work@c", "weaver|work@")
        layout = MarketLayout(keys)
        mask = labour_area_mask(layout, {"a", "c"})
        kept = {key for key, flag in zip(layout.keys_grouped, mask.tolist()) if flag}
        self.assertEqual(kept, {"smith|work@a", "weaver|work@c"})


class TradedVolumes(unittest.TestCase):
    def test_a_countrys_volumes_equal_the_market_by_market_sum_in_value_and_key_order(self):
        map_of = area_map()
        areas = [area.area_id for good in ("grain", "gold") for area in map_of.areas(good)]
        volumes = {good + KEY_SEPARATOR + area: 0.1 * (index + 1) for index, (good, area) in enumerate(
            (good, area) for good in ("iron", "grain", "gold", "iron_ore", "unmapped") for area in areas + ["work@a"])}
        economy = types.SimpleNamespace(record=types.SimpleNamespace(goods=types.SimpleNamespace(volumes=volumes)), area_map=map_of,
                                        setup=types.SimpleNamespace(tiles=TILES, tiles_of=lambda country: {"home": ("a", "b"), "away": ("c",)}[country]))
        for country in (None, "home", "away"):
            new, old = _traded_volumes(economy, country), _traded_volumes_by_market(economy, country)
            self.assertEqual(list(new), list(old), country)
            self.assertEqual(new, old, country)

    def test_no_volumes_is_no_totals(self):
        economy = types.SimpleNamespace(record=types.SimpleNamespace(goods=types.SimpleNamespace(volumes={})), area_map=area_map(),
                                        setup=types.SimpleNamespace(tiles=TILES))
        self.assertEqual(_traded_volumes(economy, None), {})


if __name__ == "__main__":
    unittest.main()
