"""Speed: the national price (`national_prices.national_prices`) and wage read through the cached market layout agree with
the plain per-call scan they replaced, on random remembered markets; no game. The sums are `math.fsum` in both, so the
figures are equal, not just close."""

QUICK_TOPIC = True

import math
import random
import types
import unittest

from sim.economy.market_memory import KEY_SEPARATOR, RECENT_TRADE_YEARS, MarketMemory
from sim.economy.national_prices import national_prices, national_wages


def plain_national_prices(record, keep):
    """The scan `national_prices` ran before the cached layout: every call split, sorted and tested every market."""
    memory = record.memory
    weights = memory.volume_weights or record.goods.volumes
    by_good = {}
    for key, price in sorted(memory.prices.items()):
        good, area = key.split(KEY_SEPARATOR, 1)
        if keep is None or keep(good, area):
            by_good.setdefault(good, []).append((price, memory.traded_within(key, RECENT_TRADE_YEARS), weights.get(key, 0.0)))
    prices = {}
    for good, markets in by_good.items():
        value = math.fsum(price * weight for price, traded, weight in markets if traded)
        quantity = math.fsum(weight for _price, traded, weight in markets if traded)
        prices[good] = value / quantity if quantity > 0.0 else markets[0][0]
    return prices


def plain_national_wages(record, keep):
    """The scan `national_wages` ran before the cached layout."""
    rows = {}
    for key, wage in sorted(record.memory.wages.items()):
        if keep is None or keep(key):
            trade, area = key.split(KEY_SEPARATOR, 1)
            people = math.fsum(record.labour.workforce.workers.get(area, {}).get(trade, ()))
            rows.setdefault(trade, []).append((wage, record.labour.hours_cleared_in(key), people))
    wages = {}
    for trade, entries in rows.items():
        for weight_index in (1, 2):
            total = math.fsum(entry[weight_index] for entry in entries)
            if total > 0.0:
                wages[trade] = math.fsum(entry[0] * entry[weight_index] for entry in entries) / total
                break
        else:
            wages[trade] = math.fsum(entry[0] for entry in entries) / len(entries)
    return dict(sorted(wages.items()))


def random_record(rng):
    goods = ["grain", "iron", "iron_ore", "salt", "wool", "tin", "oil"][:rng.randint(1, 7)]
    areas = ["a", "b", "c", "d", "e"][:rng.randint(1, 5)]
    keys = [good + KEY_SEPARATOR + area for good in goods for area in areas if rng.random() < 0.8]
    rng.shuffle(keys)
    memory = MarketMemory(prices={key: rng.uniform(0.1, 50.0) for key in keys},
                          wages={key: rng.uniform(0.1, 5.0) for key in keys if rng.random() < 0.8},
                          trade_age={key: rng.randint(0, 4) for key in keys if rng.random() < 0.7},
                          volume_weights={key: rng.choice([0.0, rng.uniform(0.1, 20.0)]) for key in keys if rng.random() < 0.8})
    workers = {area: {good: [rng.uniform(0.0, 9.0) for _ in range(2)] for good in goods if rng.random() < 0.5} for area in areas}
    hired = {key.split(KEY_SEPARATOR)[1]: {key.split(KEY_SEPARATOR)[0]: {"x": rng.choice([0.0, rng.uniform(1.0, 40.0)])}}
             for key in keys if rng.random() < 0.5}
    labour = types.SimpleNamespace(
        workforce=types.SimpleNamespace(workers=workers),
        hours_cleared_in=lambda key: math.fsum(hired.get(key.split(KEY_SEPARATOR)[1], {}).get(key.split(KEY_SEPARATOR)[0], {}).values()))
    return types.SimpleNamespace(memory=memory, goods=types.SimpleNamespace(volumes={}), labour=labour)


class NationalFiguresAgreeWithThePlainScan(unittest.TestCase):

    def test_prices_with_and_without_a_filter(self):
        rng = random.Random(3)
        for _case in range(200):
            record = random_record(rng)
            blocked = {rng.choice(["a", "b", "c"]) for _ in range(rng.randint(0, 2))}
            keep = None if rng.random() < 0.3 else (lambda _good, area, blocked=blocked: area not in blocked)
            for _repeat in range(2):    # the second ask is served from the kept layout and mask
                token = None if keep is None else frozenset(blocked)
                self.assertEqual(national_prices(record, keep, keep_token=token), plain_national_prices(record, keep))

    def test_wages_with_and_without_a_filter(self):
        rng = random.Random(4)
        for _case in range(200):
            record = random_record(rng)
            blocked = {rng.choice(["a", "b", "c"]) for _ in range(rng.randint(0, 2))}
            keep = None if rng.random() < 0.3 else (lambda key, blocked=blocked: key.split(KEY_SEPARATOR)[1] not in blocked)
            for _repeat in range(2):
                token = None if keep is None else frozenset(blocked)
                self.assertEqual(national_wages(record, keep, keep_token=token), plain_national_wages(record, keep))

    def test_a_changed_price_is_read_fresh(self):
        record = random_record(random.Random(5))
        before = national_prices(record)
        key = next(iter(record.memory.prices))
        record.memory.prices[key] += 100.0
        record.memory.trade_age[key] = 0
        record.memory.volume_weights[key] = 5.0
        self.assertEqual(national_prices(record), plain_national_prices(record, None))
        self.assertNotEqual(national_prices(record), before)

    def test_a_kept_answer_cannot_be_changed_by_a_caller(self):
        record = random_record(random.Random(6))
        first = national_prices(record, keep=None)
        expected = dict(first)
        first.clear()
        self.assertEqual(national_prices(record, keep=None), expected)

    def test_holds_wage_for_follows_the_wages_held_now(self):
        held = MarketMemory(wages={"smith|a": 1.0, "smith|b": 1.0, "smithy|a": 2.0})
        self.assertTrue(held.holds_wage_for("smith"))
        del held.wages["smith|a"]
        self.assertTrue(held.holds_wage_for("smith"))      # another area still holds one
        del held.wages["smith|b"]
        self.assertFalse(held.holds_wage_for("smith"))      # "smithy" is another trade
        self.assertFalse(MarketMemory().holds_wage_for("smith"))
        self.assertTrue(held.holds_wage_for("smithy"))

    def test_no_markets_no_figures(self):
        record = types.SimpleNamespace(memory=MarketMemory(), goods=types.SimpleNamespace(volumes={}), labour=None)
        self.assertEqual(national_prices(record), {})
        self.assertEqual(national_wages(record), {})


if __name__ == "__main__":
    unittest.main()
