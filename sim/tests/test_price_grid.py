"""The offered-price grid (sim/economy/price_grid.py): the kernel on written-out rows, and the grid and a tile's block against
`YearView.offered_price(good, area_of(good, tile))` good by good, including after each kind of write to the memory."""

QUICK_TOPIC = True

import math
import unittest

import numpy

from sim.economy.market_memory import KEY_SEPARATOR
from sim.economy.price_grid import PriceGrid, price_index_of
from sim.economy.price_grid_kernels import offered_by_good_tile
from sim.economy.priced_reads import offered_prices_for, tile_price_reader, usual_prices_for
from sim.economy.types import QUOTE_LOWEST_UNFILLED_ASK
from sim.tests.year_close_fixture import GOODS, TILES, economy_of

NAN = numpy.nan


class OfferedByGoodTile(unittest.TestCase):
    def test_each_cell_is_the_offered_price_of_its_market_and_nan_where_there_is_none(self):
        offered_by_market = numpy.array([1.5, NAN, 3.0])
        market_of_good_tile = numpy.array([[0, 2, -1], [1, 1, 0]])
        grid = offered_by_good_tile(offered_by_market, market_of_good_tile)
        numpy.testing.assert_array_equal(grid, numpy.array([[1.5, 3.0, NAN], [NAN, NAN, 1.5]]))

    def test_a_market_row_past_the_prices_is_no_price_not_a_wrong_cell(self):
        grid = offered_by_good_tile(numpy.array([2.0]), numpy.array([[0, 5]]))
        numpy.testing.assert_array_equal(grid, numpy.array([[2.0, NAN]]))

    def test_no_goods_is_an_empty_grid(self):
        self.assertEqual(offered_by_good_tile(numpy.empty(0), numpy.empty((0, 3), dtype=numpy.int64)).shape, (0, 3))


def scalar_prices(view, tile):
    return {good: view.offered_price(good, view.area_of(good, tile)) for good in GOODS}


def block_prices(view, tile):
    block = view.offered_prices_on(tile)
    return {good: block.prices.get(good) for good in GOODS}


class GridAgainstTheScalarRead(unittest.TestCase):
    def test_every_good_on_every_tile_has_the_price_offered_price_gives(self):
        for seed in range(8):
            _setup, _record, view, _ledger, _area_map = economy_of(seed)
            for tile in TILES:
                self.assertEqual(block_prices(view, tile), scalar_prices(view, tile))

    def test_the_block_holds_only_goods_that_have_a_price(self):
        _setup, _record, view, _ledger, _area_map = economy_of(1)
        for tile in TILES:
            self.assertTrue(all(price is not None and not math.isnan(price) for price in view.offered_prices_on(tile).prices.values()))

    def test_a_tile_the_area_map_does_not_hold_has_no_block_and_is_read_good_by_good(self):
        _setup, _record, view, _ledger, _area_map = economy_of(2)
        self.assertIsNone(view.offered_prices_on("nowhere"))
        self.assertEqual(offered_prices_for(view, "nowhere", GOODS), scalar_prices(view, "nowhere"))

    def test_offered_prices_for_names_every_good_asked_with_none_for_no_price(self):
        _setup, _record, view, _ledger, _area_map = economy_of(3)
        asked = list(GOODS) + ["unlisted_good"]
        found = offered_prices_for(view, TILES[0], asked)
        self.assertEqual(set(found), set(asked))
        self.assertEqual({good: found[good] for good in GOODS}, scalar_prices(view, TILES[0]))

    def test_a_good_the_area_map_has_no_market_for_is_read_by_itself(self):
        _setup, record, view, _ledger, _area_map = economy_of(3)
        record.memory.prices["unlisted_good" + KEY_SEPARATOR + view.area_of("unlisted_good", TILES[0])] = 4.0
        reader = tile_price_reader(view, TILES[0])((("unlisted_good", 1.0),))
        self.assertEqual(reader("unlisted_good"), view.offered_price("unlisted_good", view.area_of("unlisted_good", TILES[0])))
        self.assertEqual(offered_prices_for(view, TILES[0], ["unlisted_good"]), {"unlisted_good": 4.0})

    def test_a_good_with_no_market_anywhere_has_no_price_without_a_per_good_read(self):
        _setup, _record, view, _ledger, _area_map = economy_of(3)
        reader = tile_price_reader(view, TILES[0])((("unlisted_good", 1.0),))
        self.assertIsNone(reader("unlisted_good"))
        self.assertIsNone(view.offered_price("unlisted_good", view.area_of("unlisted_good", TILES[0])))
        self.assertIs(reader.__self__, view.offered_prices_on(TILES[0]).prices)


class RememberedPrices(unittest.TestCase):
    def test_every_good_on_every_tile_has_the_price_price_gives(self):
        for seed in range(8):
            _setup, _record, view, _ledger, _area_map = economy_of(seed)
            for tile in TILES:
                found = view.remembered_prices_on(tile).prices
                self.assertEqual({good: found.get(good) for good in GOODS}, {good: view.price(good, view.area_of(good, tile)) for good in GOODS})

    def test_present_prices_at_is_the_per_good_read_in_the_order_of_the_names(self):
        for seed in range(8):
            _setup, _record, view, _ledger, _area_map = economy_of(seed)
            names = tuple(reversed(GOODS))
            for tile in TILES:
                self.assertEqual(list(view.present_prices_at(names, tile).items()), list(view._present_prices_by_key(names, tile).items()))

    def test_present_prices_at_follows_a_price_written_after_it_was_read(self):
        _setup, record, view, _ledger, area_map = economy_of(5)
        names = (GOODS[0], GOODS[1])
        view.present_prices_at(names, TILES[0])
        record.memory.set_price(GOODS[0] + KEY_SEPARATOR + area_map.area_of(GOODS[0], TILES[0]), 55.5)
        self.assertEqual(view.present_prices_at(names, TILES[0])[GOODS[0]], 55.5)

    def test_names_outside_the_area_map_are_read_by_key(self):
        _setup, record, view, _ledger, _area_map = economy_of(5)
        record.memory.prices["unlisted_good" + KEY_SEPARATOR + view.area_of("unlisted_good", TILES[0])] = 3.5
        names = (GOODS[0], "unlisted_good")
        self.assertEqual(view.present_prices_at(names, TILES[0]), view._present_prices_by_key(names, TILES[0]))


class UsualPrices(unittest.TestCase):
    def test_every_good_on_every_tile_has_the_price_usual_price_gives(self):
        held = 0
        for seed in range(8):
            _setup, record, view, _ledger, area_map = economy_of(seed)
            for number, good in enumerate(GOODS):         # a usual price for some markets (the fixture may hold none)
                if number % 2 == 0:
                    record.memory.usual_prices[good + KEY_SEPARATOR + area_map.area_of(good, TILES[0])] = 1.5 + number
            for tile in TILES:
                found = view.usual_prices_on(tile).prices
                expected = {good: view.usual_price(good, view.area_of(good, tile)) for good in GOODS}
                self.assertEqual({good: found.get(good) for good in GOODS}, expected)
                self.assertEqual(usual_prices_for(view, tile, GOODS), expected)
                held += sum(1 for price in expected.values() if price is not None)
        self.assertGreater(held, 8)

    def test_a_usual_price_written_after_it_was_read_is_seen(self):
        _setup, record, view, _ledger, area_map = economy_of(5)
        key = GOODS[0] + KEY_SEPARATOR + area_map.area_of(GOODS[0], TILES[0])
        self.assertNotIn(GOODS[0], view.usual_prices_on(TILES[0]).prices)
        record.memory.usual_prices[key] = 9.25
        self.assertEqual(view.usual_prices_on(TILES[0]).prices[GOODS[0]], 9.25)
        record.memory.usual_prices.pop(key)
        self.assertNotIn(GOODS[0], view.usual_prices_on(TILES[0]).prices)

    def test_a_tile_the_area_map_does_not_hold_and_an_unlisted_good_are_read_by_themselves(self):
        _setup, _record, view, _ledger, _area_map = economy_of(2)
        self.assertIsNone(view.usual_prices_on("nowhere"))
        self.assertEqual(usual_prices_for(view, "nowhere", GOODS), {good: view.usual_price(good, view.area_of(good, "nowhere")) for good in GOODS})
        self.assertEqual(usual_prices_for(view, TILES[0], ["unlisted_good"]), {"unlisted_good": view.usual_price("unlisted_good", view.area_of("unlisted_good", TILES[0]))})


class GridFollowsTheMemory(unittest.TestCase):
    def setUp(self):
        _setup, self.record, self.view, _ledger, self.area_map = economy_of(4)
        self.memory = self.record.memory
        self.key = GOODS[0] + KEY_SEPARATOR + self.area_map.area_of(GOODS[0], TILES[0])

    def test_a_price_set_through_the_memory_is_seen(self):
        before = self.view.offered_prices_on(TILES[0]).prices.get(GOODS[0])
        self.memory.set_price(self.key, 123.0)
        self.memory.note_trading([self.key])
        self.assertEqual(self.view.offered_prices_on(TILES[0]).prices[GOODS[0]], 123.0)
        self.assertNotEqual(before, 123.0)

    def test_a_price_written_through_the_store_alone_is_seen(self):
        self.memory.note_trading([self.key])
        self.view.offered_prices_on(TILES[0])
        self.memory.prices[self.key] = 77.0
        self.assertEqual(self.view.offered_prices_on(TILES[0]).prices[GOODS[0]], 77.0)

    def test_a_trade_age_and_a_quote_kind_decide_what_is_on_offer(self):
        self.memory.prices[self.key] = 5.0
        self.memory.trade_age[self.key] = 3
        self.memory.drop_quote_kind(self.key)
        self.assertNotIn(GOODS[0], self.view.offered_prices_on(TILES[0]).prices)
        self.memory.set_quote_kind(self.key, QUOTE_LOWEST_UNFILLED_ASK)
        self.assertEqual(self.view.offered_prices_on(TILES[0]).prices[GOODS[0]], 5.0)

    def test_a_removed_price_is_gone(self):
        self.memory.prices[self.key] = 5.0
        self.memory.note_trading([self.key])
        self.assertIn(GOODS[0], self.view.offered_prices_on(TILES[0]).prices)
        self.memory.prices.pop(self.key)
        self.assertNotIn(GOODS[0], self.view.offered_prices_on(TILES[0]).prices)

    def test_a_market_numbered_after_the_grid_was_read_is_found(self):
        self.view.offered_prices_on(TILES[0])
        self.memory.prices["good3|brand_new"] = 2.0
        self.memory.prices[GOODS[3] + KEY_SEPARATOR + self.area_map.area_of(GOODS[3], TILES[1])] = 6.0
        self.memory.note_trading([GOODS[3] + KEY_SEPARATOR + self.area_map.area_of(GOODS[3], TILES[1])])
        self.assertEqual(block_prices(self.view, TILES[1]), scalar_prices(self.view, TILES[1]))

    def test_the_grid_is_filled_again_only_after_a_write(self):
        grid = PriceGrid(self.memory, price_index_of(self.area_map))
        grid.on_tile(TILES[0])
        grid.on_tile(TILES[1])
        self.assertEqual(grid.refreshes, 1)
        self.memory.prices[self.key] = 9.5
        grid.on_tile(TILES[0])
        self.assertEqual(grid.refreshes, 2)


if __name__ == "__main__":
    unittest.main()
