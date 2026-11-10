"""`YearView.wages_at` reads the wage rule's table by the labour area's column: each trade's wage equals the rule cell by cell
(`trade_wages.wage_in_view`), also after the memory is written to, and a trade the setup does not know is refused as the rule refuses it."""

QUICK_TOPIC = True

import unittest

from sim.economy.market_memory import KEY_SEPARATOR
from sim.economy.setup import labour_area
from sim.economy.trade_wages import wage_in_area
from sim.tests.year_close_fixture import TILES, TRADES, economy_of


class WagesAtColumn(unittest.TestCase):
    def test_each_wage_equals_the_rule_for_the_trade_in_the_tiles_labour_area(self):
        for seed in range(6):
            setup, record, view, _ledger, _area_map = economy_of(seed)
            trades = tuple(TRADES)
            for tile in TILES:
                found = view.wages_at(trades, tile)
                self.assertEqual(list(found), list(trades))
                for trade in trades:
                    self.assertEqual(found[trade], wage_in_area(setup, record.memory, trade, labour_area(tile)), (seed, tile, trade))

    def test_a_write_to_the_wages_is_seen(self):
        setup, record, view, _ledger, _area_map = economy_of(1)
        trades = tuple(TRADES)
        before = view.wages_at(trades, TILES[0])
        record.memory.wages["smith" + KEY_SEPARATOR + labour_area(TILES[0])] = 77.0
        record.memory.set_rate("coin", 0.05)
        after = view.wages_at(trades, TILES[0])
        for trade in trades:
            self.assertEqual(after[trade], wage_in_area(setup, record.memory, trade, labour_area(TILES[0])))
        self.assertEqual(after["smith"], 77.0)
        self.assertNotEqual(before["smith"], 77.0)

    def test_an_unknown_trade_is_refused(self):
        _setup, _record, view, _ledger, _area_map = economy_of(0)
        with self.assertRaises(KeyError):
            view.wages_at(("labourer", "nobody"), TILES[0])


if __name__ == "__main__":
    unittest.main()
