"""Readers of the market memory's columns (sim/economy/market_column_kernels.py, `notional._traded_volumes`,
`national_prices.remembered_columns`) against the per-key reads they replaced, on markets written out in the test."""

QUICK_TOPIC = True

import types
import unittest

import numpy

from sim.economy import notional
from sim.economy.market_column_kernels import add_in_order_by_group
from sim.economy.market_memory import RECENT_TRADE_YEARS, MarketMemory
from sim.economy.market_store import figures_for
from sim.economy.national_prices import remembered_columns


class AddInOrderByGroup(unittest.TestCase):
    def test_each_group_is_added_left_to_right_and_groups_are_listed_as_first_met(self):
        totals, first_seen, appeared = add_in_order_by_group(numpy.array([2, 0, 2, 2]), numpy.array([0.1, 5.0, 0.2, 0.3]), 4)
        self.assertEqual((totals.tolist(), first_seen.tolist(), appeared), ([5.0, 0.0, 0.1 + 0.2 + 0.3, 0.0], [2, 0, -1, -1], 2))

    def test_the_sum_is_the_float_a_running_total_gives_not_a_compensated_one(self):
        values = numpy.array([1e16, 1.0, 1.0, -1e16])
        totals, _first, _appeared = add_in_order_by_group(numpy.zeros(4, dtype=numpy.int64), values, 1)
        running = 0.0
        for value in values.tolist():
            running += value
        self.assertEqual(totals[0], running)

    def test_no_markets_is_no_groups(self):
        totals, first_seen, appeared = add_in_order_by_group(numpy.empty(0, dtype=numpy.int64), numpy.empty(0), 2)
        self.assertEqual((totals.tolist(), first_seen.tolist(), appeared), ([0.0, 0.0], [-1, -1], 0))


def record_of(volume_weights, volumes):
    memory = MarketMemory(prices={key: 1.0 for key in volume_weights}, volume_weights=volume_weights,
                          trade_age={"tin|b": 1, "tin|a": 3})
    return types.SimpleNamespace(memory=memory, goods=types.SimpleNamespace(volumes=volumes))


class TradedVolumes(unittest.TestCase):
    def test_the_memorys_usual_volumes_are_read_from_the_columns_as_the_keys_were(self):
        weights = {"wool|b": 0.1, "tin|a": 4.0, "wool|a": 0.2, "tin|b": 2.5, "salt|a": 0.3, "wool|c": 0.3}
        record = record_of(weights, {"wool|b": 9.0, "tin|a": 1.5, "wool|a": 0.05, "wool|c": 0.7})
        found = notional._traded_volumes(record)
        by_key = notional._traded_volumes_by_key(record, record.memory.volume_weights)
        self.assertEqual((list(found), found), (list(by_key), by_key))

    def test_volumes_that_are_not_the_memorys_are_read_by_key(self):
        record = record_of({}, {"wool|b": 3.0, "tin|a": 1.5})
        self.assertEqual(notional._traded_volumes(record), {"wool": 3.0, "tin": 1.5})

    def test_a_good_numbered_but_with_no_usual_volume_is_not_a_key(self):
        record = record_of({"wool|a": 2.0}, {})
        record.memory.prices["tin|a"] = 3.0
        self.assertEqual(notional._traded_volumes(record), {"wool": 0.0})


class RememberedColumns(unittest.TestCase):
    def test_price_volume_and_age_of_each_market_in_the_order_of_the_keys(self):
        weights = {"wool|b": 0.1, "tin|a": 4.0, "wool|a": 0.2}
        record = record_of(weights, {})
        memory = record.memory
        memory.prices["tin|b"] = 7.0
        keys = tuple(memory.prices)
        price, volume, age = remembered_columns(memory, memory.volume_weights, keys)
        self.assertEqual(price.tolist(), [memory.prices[key] for key in keys])
        self.assertEqual(volume.tolist(), figures_for(memory.volume_weights, keys, 0.0))
        self.assertEqual(age.tolist(), figures_for(memory.trade_age, keys, RECENT_TRADE_YEARS + 1))

    def test_volumes_that_are_not_the_memorys_are_read_by_key(self):
        record = record_of({}, {"wool|a": 5.0})
        record.memory.prices["wool|a"] = 2.0
        keys = tuple(record.memory.prices)
        self.assertEqual(remembered_columns(record.memory, record.goods.volumes, keys)[1].tolist(), figures_for(record.goods.volumes, keys, 0.0))


if __name__ == "__main__":
    unittest.main()
