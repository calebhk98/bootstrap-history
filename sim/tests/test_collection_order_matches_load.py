"""A live game's keyed stores iterate in the order a save-and-load gives, whatever order the entries were made in,
so a float sum or a per-entry draw over them cannot differ between a live and a resumed game."""

QUICK_TOPIC = True

import unittest

from sim.agents.records import ActorsState
from sim.agents.registry import ActorRegistry
from sim.economy.accounts import Book
from sim.economy.market_memory import MarketMemory
from sim.economy.producers import Producer
from sim.economy.record import EconomyRecord
from sim.economy.types import CurrencySpec

IDS = ["p_c", "p_a", "p_b", "p_e", "p_d"]
VALUES = {"p_a": 1e16, "p_b": 1.0, "p_c": 3e-3, "p_d": 7e8, "p_e": 1e-5}


def _record_made_in(order):
    record = EconomyRecord(book=Book(), memory=MarketMemory(), currency=CurrencySpec("coin", "fiat", None, 0.0, None))
    for producer_id in order:
        record.producers[producer_id] = Producer(producer_id, "o", "r", "t", VALUES[producer_id])
        record.shares[producer_id] = {"h_b": 1.0, "h_a": 2.0}
    return record


class CollectionOrderTest(unittest.TestCase):
    def test_record_stores_iterate_in_saved_order(self):
        total_by_order = []
        for order in (IDS, list(reversed(IDS))):
            record = _record_made_in(order)
            record.sort_in_saved_order()
            self.assertEqual(list(record.producers), sorted(IDS))
            self.assertEqual(list(record.shares["p_a"]), ["h_a", "h_b"])
            self.assertEqual(list(EconomyRecord.from_record(record.to_record()).producers), list(record.producers))
            total_by_order.append(sum(VALUES[producer_id] for producer_id in record.producers))
        self.assertEqual(total_by_order[0], total_by_order[1])

    def test_registry_seats_actors_in_id_order(self):
        state = ActorsState(home_country="home")
        registry = ActorRegistry(state)
        for actor_id in ("z", "a", "m"):
            registry.actors[actor_id] = actor_id
            state.records[actor_id] = actor_id
        registry._seat_in_id_order()
        self.assertEqual(list(registry.actors), ["a", "m", "z"])
        self.assertEqual(list(state.records), ["a", "m", "z"])


if __name__ == "__main__":
    unittest.main()
