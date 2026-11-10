"""`goods_settle.idle_years` (the kernel `goods_idle_years.note_idle_years`) against the memory-wrapper calls `note_idle_years` made market
by market (`count_year_without_bids`, `end_years_without_bids`, `count_year_without_offers`, `end_years_without_offers`): the counts
returned, every store's items in entry order and the tables' bookkeeping agree on written-out and random memories (under numba and
ROME_NO_JIT=1)."""
QUICK_TOPIC = True

import random
import types
import unittest

import numpy as np
from collections import namedtuple

from sim.economy import goods_good_clear, goods_settle
from sim.economy.market_memory import MarketMemory
from sim.economy.market_table_specs import STORE_COUNT

Market = namedtuple("Market", ("market", "has_offers", "has_units", "has_funded_bid"))


def memory_with(keys, rng):
    memory = MarketMemory()
    memory.tables.admit_goods_markets(keys)
    for key in rng.sample(keys, len(keys)):
        if rng.random() < 0.5:
            memory.years_without_bids[key] = rng.randrange(0, 5)
        if rng.random() < 0.5:
            memory.years_without_offers[key] = rng.randrange(0, 5)
    return memory


def shown(memory):
    return ([list(store.items()) for store in (memory.years_without_bids, memory.years_without_offers)],
            memory.tables.next_order.tolist()[:STORE_COUNT], memory.tables.member_count.tolist()[:STORE_COUNT])


def columns_of(markets):
    """The columns of a `GoodClearing` that `idle_years` reads, for these markets."""
    return types.SimpleNamespace(
        market=np.array([each.market for each in markets], dtype=np.int64), has_offers=np.array([each.has_offers for each in markets], dtype=np.bool_),
        has_units=np.array([each.has_units for each in markets], dtype=np.bool_),
        has_funded_bid=np.array([each.has_funded_bid for each in markets], dtype=np.bool_))


class IdleYearsAreTheWrapperCounts(unittest.TestCase):

    def test_a_market_with_offers_and_no_bids_counts_a_year_and_one_with_bids_ends_its_count(self):
        memory = MarketMemory()
        memory.years_without_bids["g|a"] = 2
        memory.years_without_offers["g|b"] = 3
        memory.tables.admit_goods_markets(["g|a", "g|b"])
        rows = [memory.tables.goods_numbers["g|a"], memory.tables.goods_numbers["g|b"]]
        before = goods_settle.idle_years(memory, columns_of([Market(rows[0], True, True, False), Market(rows[1], True, True, True)]))
        self.assertEqual((before, dict(memory.years_without_bids), dict(memory.years_without_offers)), ([2, 3], {"g|a": 3}, {}))

    def test_random_memories_agree_with_the_wrapper_counts(self):
        for seed in range(80):
            rng = random.Random(seed)
            keys = sorted("%s|%s" % (good, area) for good in "abcd" for area in "xyz")
            fast, plain = memory_with(keys, random.Random(seed + 500)), memory_with(keys, random.Random(seed + 500))
            chosen = [key for key in keys if rng.random() < 0.7]
            flags = [(rng.random() < 0.6, rng.random() < 0.6, rng.random() < 0.6) for _ in chosen]
            markets = [Market(fast.tables.goods_numbers[key], *each) for key, each in zip(chosen, flags)]
            got = goods_settle.idle_years(fast, columns_of(markets))
            expected = [reference_count(plain, key, each) for key, each in zip(chosen, flags)]
            self.assertEqual(got, expected, seed)
            self.assertEqual(shown(fast), shown(plain), seed)


def reference_count(memory, key, flags):
    """`goods_good_clear.note_idle_years` of a market with these (has offers, has units, has a funded bid)."""
    cleared = namedtuple("Cleared", ("has_offers", "has_units", "has_funded_bid"))(*flags)
    return goods_good_clear.note_idle_years(memory, key, cleared)


if __name__ == "__main__":
    unittest.main()
