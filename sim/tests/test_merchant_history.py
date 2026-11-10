"""`MerchantTable._history_by_name` (one merchant's rows found by numpy) gives what visiting every key gave."""

QUICK_TOPIC = True

import random
import unittest

from sim.economy.market_tables import MarketTables
from sim.economy.merchant_table import MerchantTable
from sim.tests.merchant_history_reference import history_by_name


def _table_with_histories(histories):
    """A merchant table whose merchants 0.. hold {(good, area): prices}."""
    table = MerchantTable.of(MarketTables())
    for row, held in enumerate(histories):
        table.agents.append("merchant%d" % row)
        table.set_history(row, held)
    return table


class HistoryByNameTests(unittest.TestCase):
    def test_written_out_histories(self):
        table = _table_with_histories([{("wheat", "rome"): [1.0, 2.0], ("iron", "ostia"): [3.0]}, {}, {("wheat", "rome"): [4.5]}])
        for only_row in (None, 0, 1, 2, 3):
            self.assertEqual(table._history_by_name(table.numbering, only_row), history_by_name(table, table.numbering, only_row))
        self.assertEqual(table.history_of(2), {("wheat", "rome"): [4.5]})
        self.assertEqual(table.history_of(1), {})

    def test_random_histories(self):
        for seed in range(25):
            generator = random.Random(seed)
            histories = [{(generator.choice(["wheat", "iron", "salt"]), generator.choice(["rome", "ostia", "capua"])):
                          [generator.random() for _ in range(generator.randint(0, 4))] for _ in range(generator.randint(0, 5))}
                         for _ in range(generator.randint(1, 6))]
            table = _table_with_histories(histories)
            for only_row in [None] + list(range(len(histories) + 1)):
                self.assertEqual(table._history_by_name(table.numbering, only_row), history_by_name(table, table.numbering, only_row), seed)


if __name__ == "__main__":
    unittest.main()
