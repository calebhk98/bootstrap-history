"""Stage 3 of the one-price-owner plan (Complaint 507): the economy answers what a good costs on a tile, how far a
larger order moves that price, and how much the sellers there hold. A hand-built economy; no engine."""
import math
import types
import unittest

from sim.economy import api as economy_api
from sim.economy import market_curves
from sim.economy.market_memory import market_key
from sim.tests import economy_fixture
from sim.tests.economy_fixture import FARMS, GRAIN, HILLS, TOWN

QUICK_TOPIC = True


def aged_economy(years=3):
    return economy_fixture.run(economy_fixture.small_setup(), years=years)[0]


class PriceAtTileTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.economy = aged_economy()

    def test_every_tile_prices_every_good_the_economy_shows(self):
        shown, _stale = economy_api.shown_prices_of(self.economy)
        for tile in (TOWN, FARMS, HILLS):
            prices, _stale_here = economy_api.prices_at(self.economy, tile)
            self.assertEqual(set(prices), set(shown))
            self.assertTrue(all(math.isfinite(price) and price > 0.0 for price in prices.values()))

    def test_a_tile_in_an_area_that_clears_at_a_different_price_pays_that_price(self):
        economy = aged_economy()
        memory = economy.record.memory
        real_area_map = economy.area_map
        areas = {TOWN: "west", FARMS: "east", HILLS: "east"}
        economy.area_map = types.SimpleNamespace(
            goods=real_area_map.goods, areas=real_area_map.areas,
            area_of=lambda good, tile: areas[tile] if good == GRAIN else real_area_map.area_of(good, tile))
        for area, price in (("west", 0.2), ("east", 0.6)):
            memory.prices[market_key(GRAIN, area)] = price
            memory.trade_age[market_key(GRAIN, area)] = 0
            memory.volume_weights[market_key(GRAIN, area)] = 1.0
        cheap, _ = economy_api.prices_at(economy, TOWN)
        dear, _ = economy_api.prices_at(economy, FARMS)
        same, _ = economy_api.prices_at(economy, HILLS)
        self.assertAlmostEqual(dear[GRAIN] / cheap[GRAIN], 3.0)
        self.assertEqual(dear[GRAIN], same[GRAIN])

    def test_a_tile_whose_area_has_not_cleared_lately_pays_the_shown_price(self):
        economy = aged_economy()
        memory = economy.record.memory
        area = economy.area_map.area_of(GRAIN, TOWN)
        shown, _stale = economy_api.shown_prices_of(economy)
        memory.prices[market_key(GRAIN, area)] = shown[GRAIN] * 5.0
        memory.trade_age[market_key(GRAIN, area)] = 99
        here, _ = economy_api.prices_at(economy, TOWN)
        self.assertAlmostEqual(here[GRAIN], economy_api.shown_prices_of(economy)[0][GRAIN])

    def test_a_good_the_economy_has_no_market_for_has_no_price_on_any_tile(self):
        prices, _stale = economy_api.prices_at(self.economy, TOWN)
        self.assertNotIn("cobalt_kg", prices)


class KeptBooksTests(unittest.TestCase):

    AREAS = {"a": "west", "b": "east", "c": "east", "d": "north"}

    def area_map(self):
        return types.SimpleNamespace(area_of=lambda good, tile: self.AREAS[tile])

    def test_the_port_and_each_watched_tile_keep_the_book_of_their_area(self):
        self.assertEqual(market_curves.kept_areas(self.area_map(), "a", ("c",), "g"), {"west", "east"})

    def test_two_tiles_in_one_area_keep_one_book(self):
        self.assertEqual(market_curves.kept_areas(self.area_map(), "b", ("c",), "g"), {"east"})

    def test_a_tile_the_economy_does_not_hold_keeps_nothing(self):
        self.assertEqual(market_curves.kept_areas(self.area_map(), "a", ("nowhere",), "g"), {"west"})

    def test_watching_tiles_is_remembered_for_the_next_clearing(self):
        economy = aged_economy(years=1)
        economy_api.watch_tiles(economy, [HILLS, FARMS, HILLS])
        self.assertEqual(economy.watched_tiles, (FARMS, HILLS))


class PriceResponseAtTileTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.economy = aged_economy()
        cls.tonnes = max(1.0, economy_api.offered_units(cls.economy, GRAIN, TOWN) or 1.0)

    def test_the_sellers_there_hold_a_quantity(self):
        self.assertGreater(economy_api.offered_units(self.economy, GRAIN, TOWN), 0.0)

    def test_a_good_with_no_market_has_no_offered_quantity(self):
        self.assertIsNone(economy_api.offered_units(self.economy, "cobalt_kg", TOWN))

    def test_buying_more_never_lowers_the_price_and_selling_more_never_raises_it(self):
        offered = economy_api.offered_units(self.economy, GRAIN, TOWN)
        takes = [economy_api.price_response(self.economy, GRAIN, 0.0, offered * share, tile=TOWN)
                 for share in (0.0, 0.1, 0.3, 0.6)]
        self.assertTrue(all(factor is not None for factor in takes))
        self.assertEqual(takes, sorted(takes))
        lands = [economy_api.price_response(self.economy, GRAIN, offered * share, 0.0, tile=TOWN)
                 for share in (0.0, 0.1, 0.3, 0.6)]
        self.assertEqual(lands, sorted(lands, reverse=True))
        self.assertLessEqual(lands[-1], 1.0)

    def test_taking_everything_the_sellers_hold_has_no_finite_price(self):
        offered = economy_api.offered_units(self.economy, GRAIN, TOWN)
        self.assertEqual(economy_api.price_response(self.economy, GRAIN, 0.0, offered * 2.0, tile=TOWN), math.inf)

    def test_without_a_tile_the_response_is_the_port_markets_as_before(self):
        with_port = economy_api.price_response(self.economy, GRAIN, 0.0, 1.0)
        port_tile = self.economy.setup.port_tile
        at_port = economy_api.price_response(self.economy, GRAIN, 0.0, 1.0, tile=port_tile)
        self.assertIsNotNone(with_port)
        self.assertIsNotNone(at_port)
        self.assertGreaterEqual(at_port, with_port)    # the national price moves by the port's share; the port's own by all


if __name__ == "__main__":
    unittest.main()
