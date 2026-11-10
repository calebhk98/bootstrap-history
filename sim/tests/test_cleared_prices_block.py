"""`YearView.cleared_prices_for(tile, goods)` (one block read of the tile's cleared prices) gives what `cleared_price(good, area_of(good, tile))`
gives good by good, and a write to the memory shows in the next read. Random markets of year_close_fixture; no game."""

QUICK_TOPIC = True

import unittest

from sim.economy.market_memory import KEY_SEPARATOR, note_written
from sim.economy.priced_reads import cleared_prices_for
from sim.tests.year_close_fixture import GOODS, TILES, economy_of


class ClearedPricesBlock(unittest.TestCase):

    def test_block_equals_the_prices_one_by_one(self):
        held = 0
        for seed in range(6):
            _setup, _record, view, _ledger, _area_map = economy_of(seed)
            for tile in TILES:
                found = view.cleared_prices_for(tile, GOODS)
                wanted = {good: view.cleared_price(good, view.area_of(good, tile)) for good in GOODS}
                self.assertEqual(found, wanted)
                held += sum(price is not None for price in found.values())
        self.assertGreater(held, 20)

    def test_a_write_to_the_memory_shows_in_the_next_read(self):
        _setup, record, view, _ledger, _area_map = economy_of(1)
        before = view.cleared_prices_for("T0", GOODS)
        area = view.area_of(GOODS[0], "T0")
        record.memory.cleared_prices[GOODS[0] + KEY_SEPARATOR + area] = 123.5
        note_written()
        after = cleared_prices_for(view, "T0", GOODS)
        self.assertEqual(after[GOODS[0]], 123.5)
        self.assertEqual({good: price for good, price in after.items() if good != GOODS[0]},
                         {good: price for good, price in before.items() if good != GOODS[0]})


if __name__ == "__main__":
    unittest.main()
