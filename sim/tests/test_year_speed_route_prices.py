"""The prices a merchants' route pass reads from the market memory by slot (`FloatStore.values_at`) are the prices
`get_many` gives for the same markets, with 0.0 where a market has no price or is not numbered."""

QUICK_TOPIC = True

import unittest

import numpy as np

from sim.economy.market_memory import MarketMemory


class ValuesAtTest(unittest.TestCase):
    def test_values_at_equal_get_many_with_zero_for_none(self):
        memory = MarketMemory()
        memory.prices["grain|a"] = 3.5
        memory.prices["grain|b"] = 0.0
        memory.prices["salt|a"] = 7.25
        memory.prices.pop("salt|a")
        names = ["grain|a", "grain|b", "salt|a", "wool|a"]
        numbers = memory.prices._tables.goods_numbers
        rows = np.array([numbers.get(name, -1) for name in names], np.int64)
        expected = [price or 0.0 for price in memory.prices.get_many(names, None)]
        self.assertEqual(memory.prices.values_at(rows, 0.0).tolist(), expected)
        self.assertEqual(expected, [3.5, 0.0, 0.0, 0.0])


if __name__ == "__main__":
    unittest.main()
