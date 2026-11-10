"""The ledger's numbers for the labour markets of a year (`labour_settle_year._ledger_numbers`) and the year's hours by market
(`labour_results_table.offered_by_market`) equal what the one-market-at-a-time calls gave. Called on written-out markets and a stand-in
for the market memory's numbering; no game."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

import numpy as np

from sim.economy.labour_results_table import offered_by_market
from sim.economy.labour_settle_year import _ledger_numbers
from sim.economy.types import LabourResult


class StandInTables:
    """The numbering the ledger's tables keep: a trade or a labour market is numbered where it is first asked for."""

    def __init__(self):
        self.trades = {}
        self.markets = SimpleNamespace(labour_numbers={}, labour_row_for_write=self._market)

    def trade_number(self, trade):
        return self.trades.setdefault(trade, len(self.trades))

    def _market(self, key):
        return self.markets.labour_numbers.setdefault(key, len(self.markets.labour_numbers))


class LedgerNumbers(unittest.TestCase):
    def test_new_names_are_numbered_where_their_first_market_comes(self):
        tables = StandInTables()
        tables.trades["weaver"] = 0
        tables.markets.labour_numbers["smith|work@a"] = 0
        trades, areas = ["smith", "miller", "smith", "weaver", "miller"], ["work@a", "work@a", "work@b", "work@a", "work@b"]
        trade_numbers, market_numbers = _ledger_numbers(tables, trades, areas, np.array([0, 1, 2, 4]))
        self.assertEqual(trade_numbers.tolist(), [1, 2, 1, 2])         # smith is numbered 1 at the first market, miller 2
        self.assertEqual(market_numbers.tolist(), [0, 1, 2, 3])        # the known market keeps its number; new ones follow in order
        self.assertEqual(list(tables.trades), ["weaver", "smith", "miller"])

    def test_no_markets_number_nothing(self):
        tables = StandInTables()
        trade_numbers, market_numbers = _ledger_numbers(tables, ["smith"], ["work@a"], np.zeros(0, dtype=np.int64))
        self.assertEqual((trade_numbers.tolist(), market_numbers.tolist(), tables.trades), ([], [], {}))


class OfferedByMarket(unittest.TestCase):
    def test_a_plain_list_gives_hired_plus_idle_by_trade_and_area(self):
        results = [LabourResult("smith", "work@a", "coin", 1.0, 30.0, 0.0, 10.0, ()), LabourResult("miller", "work@a", "coin", 1.0, 5.0, 0.0, 0.5, ())]
        self.assertEqual(offered_by_market(results), {("smith", "work@a"): 40.0, ("miller", "work@a"): 5.5})


if __name__ == "__main__":
    unittest.main()
