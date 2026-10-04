import dataclasses
import json
import unittest

from sim.economy.record_plain import plain
from sim.economy.producers import Producer
from sim.economy.market_memory import MarketMemory


class PlainTest(unittest.TestCase):
    def test_matches_asdict_and_shares_nothing(self):
        producer = Producer("p", "o", "r", "t", 2.0, expected_prices={"wheat_kg": 1.5})
        memory = MarketMemory(year=3, prices={"wheat_kg|a": 2.0}, trade_age={"wheat_kg|a": 1})
        for item in (producer, memory):
            self.assertEqual(plain(item), dataclasses.asdict(item))
        copy = plain(producer)
        copy["expected_prices"]["wheat_kg"] = 9.0
        self.assertEqual(producer.expected_prices["wheat_kg"], 1.5)

    def test_tuples_and_lists(self):
        value = {"a": [1, (2, {"b": 3.0})], "c": None}
        self.assertEqual(json.dumps(plain(value)), json.dumps(value))


if __name__ == "__main__":
    unittest.main()
