"""`ProducerStore.to_plain` (written a column at a time) gives what `_fields` gives row by row."""

QUICK_TOPIC = True

import json
import random
import unittest

from sim.economy.producer_store import ProducerStore
from sim.economy.producers import Producer
from sim.tests.producer_plain_reference import plain_producers


def _random_producer(generator, number):
    goods = ["wheat", "iron", "salt", "cloth"]
    trades = ["smith", "weaver", "miller"]
    return Producer(
        "firm%d" % number, generator.choice(["ann", "bob"]), generator.choice(["bread", "bar"]), generator.choice(["rome", "ostia"]),
        generator.random() * 10, generator.random(),
        {good: generator.random() for good in generator.sample(goods, generator.randint(0, 4))},
        generator.randint(0, 3), generator.random() * 5, generator.random(), generator.choice([-1.0, 2.5]), generator.random(),
        generator.choice([None, 3.0]), generator.randint(1, 4),
        tuple(generator.random() for _ in range(generator.randint(0, 5))), tuple(generator.random() for _ in range(generator.randint(0, 5))),
        generator.randint(0, 2), generator.choice([None, 1.5]),
        {trade: generator.random() for trade in generator.sample(trades, generator.randint(0, 3))})


class PlainProducersTests(unittest.TestCase):
    def test_written_out_producers(self):
        store = ProducerStore({
            "b": Producer("b", "ann", "bread", "rome", 4.0, 0.5, {"wheat": 2.0, "salt": 1.0}, 1, 3.0, 2.0, 1.5, 0.25, None, 2,
                          (1.0, 2.0), (3.0,), 0, 0.75, {"smith": 0.5}),
            "a": Producer("a", "bob", "bar", "ostia", 1.0)})
        plain = store.to_plain()
        self.assertEqual(list(plain), ["a", "b"])
        self.assertEqual(plain["b"]["net_earnings_history"], (1.0, 2.0))
        self.assertEqual(plain["b"]["expected_prices"], {"wheat": 2.0, "salt": 1.0})
        self.assertIsNone(plain["a"]["land_run_cap"])
        self.assertEqual(json.dumps(plain), json.dumps(plain_producers(store)))

    def test_empty_store(self):
        self.assertEqual(ProducerStore().to_plain(), {})

    def test_random_stores_keep_values_types_and_key_order(self):
        for seed in range(40):
            generator = random.Random(seed)
            store = ProducerStore({"firm%d" % number: _random_producer(generator, number) for number in generator.sample(range(30), 12)})
            plain, reference = store.to_plain(), plain_producers(store)
            self.assertEqual(json.dumps(plain), json.dumps(reference), seed)
            self.assertEqual(repr(plain), repr(reference), seed)


if __name__ == "__main__":
    unittest.main()
