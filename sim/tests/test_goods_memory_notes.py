"""`goods_memory_notes.write_markets` and `write_volumes` against the memory-wrapper calls `year_goods` made before (`set_quote_kind`,
`drop_quote_kind`, `set_price`, `note_usual_price`, `note_cleared`, `note_trading`, `note_volume`), on written-out and random
memories: every store's items in entry order, and the bookkeeping of the tables, must agree (under numba and ROME_NO_JIT=1)."""
QUICK_TOPIC = True

import random
import unittest

import numpy

from sim.economy import goods_memory_notes
from sim.economy.goods_memory_kernels import NO_KIND
from sim.economy.market_memory import USUAL_PRICE_SPEED, MarketMemory, market_key
from sim.economy.market_table_specs import STORE_COUNT

KINDS = ("bid ceiling", "lowest unfilled ask", "cost")
FLOOR = goods_memory_notes.PRICE_MEMORY_FLOOR_SHARE


def memory_with(keys, rng):
    """A memory whose markets hold a random selection of figures, entered in a random order."""
    memory = MarketMemory()
    memory.tables.admit_goods_markets(keys)
    for key in rng.sample(keys, len(keys)):
        if rng.random() < 0.6:
            memory.prices[key] = rng.uniform(0.5, 9.0)
        if rng.random() < 0.4:
            memory.usual_prices[key] = rng.uniform(0.5, 9.0)
        if rng.random() < 0.4:
            memory.cleared_prices[key] = rng.uniform(0.5, 9.0)
        if rng.random() < 0.5:
            memory.volume_weights[key] = rng.uniform(0.0, 50.0)
        if rng.random() < 0.5:
            memory.trade_age[key] = rng.randrange(0, 4)
        if rng.random() < 0.4:
            memory.quote_kinds[key] = rng.choice(KINDS)
    return memory


def reference_notes(memory, keys, signal, kind, from_trade, price, delivered, opening):
    """The writes `_remember_markets` made, wrapper call by wrapper call."""
    traded = []
    for place, key in enumerate(keys):
        if from_trade[place]:
            memory.drop_quote_kind(key)
        if kind[place] is not None:
            memory.set_quote_kind(key, kind[place])
        if signal[place] is not None and signal[place] > 0.0:
            floor = (signal[place] if opening[place] is None else opening[place]) * FLOOR
            memory.set_price(key, max(signal[place], floor))
            memory.note_usual_price(key)
        memory.note_cleared(key, price[place], delivered[place])
        if delivered[place] > 0.0:
            memory.drop_quote_kind(key)
            traded.append(key)
    memory.note_trading(traded)


def shown(memory):
    """Everything the memory holds, in the order each store lists it, and the tables' bookkeeping."""
    stores = {name: list(getattr(memory, name).items()) for name in
              ("prices", "usual_prices", "cleared_prices", "volume_weights", "trade_age", "quote_kinds")}
    return stores, memory.tables.next_order.tolist()[:STORE_COUNT], memory.tables.member_count.tolist()[:STORE_COUNT]


class WriteMarketsTests(unittest.TestCase):
    def test_a_trading_market_and_a_quoting_one_are_written_as_the_wrappers_wrote_them(self):
        keys = ["grain|a", "grain|b", "wine|a"]
        rng = random.Random(1)
        fast, plain = memory_with(keys, rng), memory_with(keys, random.Random(1))
        rows = goods_memory_notes.rows_of(fast, keys)
        columns = ([4.0, None, 0.0], [NO_KIND, fast.tables.kind_number("cost"), NO_KIND], [True, False, False], [4.5, None, None],
                   [3.0, 0.0, 0.0], [2.0, None, 1.0])
        goods_memory_notes.write_markets(fast, rows, *columns)
        reference_notes(plain, keys, columns[0], [None, "cost", None], columns[2], columns[3], columns[4], columns[5])
        self.assertEqual(shown(fast), shown(plain))

    def test_random_memories_and_markets_agree_with_the_wrappers(self):
        for seed in range(60):
            rng = random.Random(seed)
            keys = sorted(market_key(good, area) for good in ("a", "b", "c", "d") for area in ("x", "y", "z") if rng.random() < 0.8)
            fast, plain = memory_with(keys, random.Random(seed + 1000)), memory_with(keys, random.Random(seed + 1000))
            chosen = [key for key in keys if rng.random() < 0.8]
            signal = [rng.choice([None, 0.0, -1.0, float("nan"), rng.uniform(1e-12, 9.0)]) for _ in chosen]
            kind = [rng.choice([None, *KINDS]) for _ in chosen]
            from_trade = [rng.random() < 0.5 for _ in chosen]
            price = [rng.choice([None, 0.0, rng.uniform(0.1, 9.0)]) for _ in chosen]
            delivered = [rng.choice([0.0, 0.0, rng.uniform(0.01, 20.0)]) for _ in chosen]
            opening = [rng.choice([None, rng.uniform(1.0, 9.0), rng.uniform(1e3, 1e4)]) for _ in chosen]
            rows = goods_memory_notes.rows_of(fast, chosen)
            numbers = [goods_memory_notes.kind_number(fast, each) for each in kind]
            goods_memory_notes.write_markets(fast, rows, signal, numbers, from_trade, price, delivered, opening)
            reference_notes(plain, chosen, signal, kind, from_trade, price, delivered, opening)
            self.assertEqual(shown(fast), shown(plain), seed)

    def test_the_usual_price_moves_by_the_declared_speed(self):
        memory = MarketMemory()
        memory.prices["g|a"], memory.usual_prices["g|a"] = 1.0, 2.0
        rows = goods_memory_notes.rows_of(memory, ["g|a"])
        goods_memory_notes.write_markets(memory, rows, [4.0], [NO_KIND], [True], [None], [0.0], [None])
        self.assertEqual(memory.usual_prices["g|a"], 2.0 + USUAL_PRICE_SPEED * (4.0 - 2.0))


class WriteVolumesTests(unittest.TestCase):
    def test_volumes_move_toward_the_year_and_the_unseen_decay(self):
        memory = MarketMemory()
        memory.volume_weights["g|a"], memory.volume_weights["g|b"] = 10.0, 20.0
        rows = goods_memory_notes.rows_of(memory, ["g|a", "g|c"])
        goods_memory_notes.write_volumes(memory, rows, [4.0, 6.0])
        self.assertEqual(list(memory.volume_weights.items()),
                         [("g|a", 10.0 + 0.3 * (4.0 - 10.0)), ("g|b", 20.0 + 0.3 * (0.0 - 20.0)), ("g|c", 6.0)])

    def test_random_memories_agree_with_note_volume(self):
        for seed in range(40):
            rng = random.Random(seed)
            keys = sorted(market_key(good, area) for good in ("a", "b", "c") for area in ("x", "y", "z"))
            fast, plain = memory_with(keys, random.Random(seed)), memory_with(keys, random.Random(seed))
            chosen = sorted(rng.sample(keys, rng.randrange(0, len(keys))))
            quantity = [rng.choice([0.0, rng.uniform(0.0, 30.0)]) for _ in chosen]
            goods_memory_notes.write_volumes(fast, goods_memory_notes.rows_of(fast, chosen), quantity)
            for key, each in zip(chosen, quantity):
                plain.note_volume(key, each)
            for key in sorted(set(plain.volume_weights) - set(chosen)):
                plain.note_volume(key, 0.0)
            self.assertEqual(shown(fast), shown(plain), seed)
            self.assertTrue(numpy.array_equal(fast.tables.goods_table.volume_weight[:len(keys)],
                                              plain.tables.goods_table.volume_weight[:len(keys)], equal_nan=True))


if __name__ == "__main__":
    unittest.main()
