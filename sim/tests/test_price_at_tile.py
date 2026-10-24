"""Stage 3 of the one-price-owner plan (Complaint 507): the economy answers what a good costs on a tile, how far a
larger order moves that price, and how much the sellers there hold. Each answer is one function called on an economy
written out here (an area map, a memory of prices, the summarised book of each market); the shown prices and the national
prices are replaced by figures where `prices_at` reads them."""
import math
import types
import unittest
from unittest import mock

from sim.economy import api as economy_api
from sim.economy import market_curves
from sim.economy import prices_at as prices_at_module
from sim.economy.market_memory import market_key

QUICK_TOPIC = True

GRAIN, ORE = "grain_kg", "ore_kg"
SHOWN = {GRAIN: 0.4, ORE: 2.0}
BOOK = {"bids": [[0.0, 80.0, 1.0, 1.0, 80.0, None]], "offers": [[0.5, 100.0]]}     # the sellers hold 100


def economy_over(areas=None, prices=None, trade_age=None, curves=None):
    """An economy whose grain market is one area "a" unless `areas` says which area a tile is in."""
    areas = areas or {}
    memory = types.SimpleNamespace(prices=dict(prices or {}), trade_age=dict(trade_age or {}),
                                   volume_weights={key: 1.0 for key in (prices or {})})
    return types.SimpleNamespace(
        setup=types.SimpleNamespace(port_tile="port", country_of=lambda tile: "home"),
        area_map=types.SimpleNamespace(area_of=lambda good, tile: areas.get(tile, "a") if good == GRAIN else "other"),
        record=types.SimpleNamespace(memory=memory, curves=dict(curves or {}), volumes={}))


def prices_on(economy, tile, shown=None, stale=()):
    with mock.patch.object(prices_at_module.country_figures, "prices", return_value=dict(shown or SHOWN)), \
            mock.patch.object(prices_at_module, "shown_prices", return_value=(dict(shown or SHOWN), set(stale))):
        return economy_api.prices_at(economy, tile)


class PriceAtTileTests(unittest.TestCase):
    def test_every_tile_prices_every_good_the_economy_shows(self):
        for tile in ("town", "farms", "hills"):
            prices, stale = prices_on(economy_over(), tile)
            self.assertEqual(prices, SHOWN)
            self.assertTrue(all(math.isfinite(price) and price > 0.0 for price in prices.values()))
            self.assertEqual(stale, set())

    def test_a_tile_in_an_area_that_clears_at_a_different_price_pays_that_price(self):
        economy = economy_over({"town": "west", "farms": "east", "hills": "east"},
                               prices={market_key(GRAIN, "west"): 0.2, market_key(GRAIN, "east"): 0.6},
                               trade_age={market_key(GRAIN, "west"): 0, market_key(GRAIN, "east"): 0})
        cheap, _ = prices_on(economy, "town")
        dear, _ = prices_on(economy, "farms")
        same, _ = prices_on(economy, "hills")
        self.assertAlmostEqual(dear[GRAIN] / cheap[GRAIN], 3.0)
        self.assertEqual(dear[GRAIN], same[GRAIN])

    def test_a_tile_whose_area_has_not_cleared_lately_pays_the_shown_price(self):
        economy = economy_over(prices={market_key(GRAIN, "a"): SHOWN[GRAIN] * 5.0}, trade_age={market_key(GRAIN, "a"): 99})
        here, _ = prices_on(economy, "town")
        self.assertAlmostEqual(here[GRAIN], SHOWN[GRAIN])

    def test_a_good_the_economy_has_no_market_for_has_no_price_on_any_tile(self):
        prices, _stale = prices_on(economy_over(), "town")
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
        economy = types.SimpleNamespace()
        economy_api.watch_tiles(economy, ["hills", "farms", "hills"])
        self.assertEqual(economy.watched_tiles, ("farms", "hills"))


class PriceResponseAtTileTests(unittest.TestCase):

    def economy(self):
        key = market_key(GRAIN, "a")
        return economy_over(prices={key: 1.0}, curves={key: BOOK})

    def test_the_sellers_there_hold_a_quantity(self):
        self.assertEqual(economy_api.offered_units(self.economy(), GRAIN, "town"), 100.0)

    def test_a_good_with_no_market_has_no_offered_quantity(self):
        self.assertIsNone(economy_api.offered_units(self.economy(), "cobalt_kg", "town"))

    def test_buying_more_never_lowers_the_price_and_selling_more_never_raises_it(self):
        economy, offered = self.economy(), 100.0
        takes = [economy_api.price_response(economy, GRAIN, 0.0, offered * share, tile="town") for share in (0.0, 0.1, 0.3, 0.6)]
        self.assertTrue(all(factor is not None for factor in takes))
        self.assertEqual(takes, sorted(takes))
        lands = [economy_api.price_response(economy, GRAIN, offered * share, 0.0, tile="town") for share in (0.0, 0.1, 0.3, 0.6)]
        self.assertEqual(lands, sorted(lands, reverse=True))
        self.assertLessEqual(lands[-1], 1.0)

    def test_taking_everything_the_sellers_hold_has_no_finite_price(self):
        self.assertEqual(economy_api.price_response(self.economy(), GRAIN, 0.0, 200.0, tile="town"), math.inf)

    def test_without_a_tile_the_response_is_the_port_markets_as_before(self):
        economy = self.economy()
        economy.area_map = types.SimpleNamespace(area_of=lambda good, tile: "a")
        key = market_key(GRAIN, "a")
        economy.record.memory.prices[key] = 1.0
        economy.record.memory.prices[market_key(GRAIN, "b")] = 1.0     # a second market the port's price is weighed against
        economy.record.memory.volume_weights[market_key(GRAIN, "b")] = 1.0
        with_port = economy_api.price_response(economy, GRAIN, 0.0, 1.0)
        at_port = economy_api.price_response(economy, GRAIN, 0.0, 1.0, tile="port")
        self.assertIsNotNone(with_port)
        self.assertGreaterEqual(at_port, with_port)    # the national price moves by the port's share; the port's own by all


if __name__ == "__main__":
    unittest.main()
