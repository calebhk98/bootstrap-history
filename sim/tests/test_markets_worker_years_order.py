"""`ProducerReads.worker_years_by_recipe` sums in producer id order, whatever order the live economy holds them in."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace
from unittest import mock

from sim.economy.producer_store import ProducerStore
from sim.economy.producers import Producer
from sim.markets import reads_producers
from sim.markets.reads_producers import ProducerReads

# runs chosen so the float sum depends on the order
RUNS = {"a": 1.0e16, "b": 1.0, "c": -1.0e16, "d": 1.0}
RECIPE = SimpleNamespace(labour_hours={"hand": 1.0})


def years_when_held_in(order):
    producers = ProducerStore({name: Producer(name, "owner", "r", "tile", RUNS[name]) for name in order})
    economy = SimpleNamespace(record=SimpleNamespace(producers=producers), setup=SimpleNamespace(countries=lambda: ["home"], recipes={"r": RECIPE}))
    agent = SimpleNamespace(economy=lambda: economy)
    with mock.patch.multiple(reads_producers.economy_api, working_hours_per_year=lambda economy: 1.0):
        return ProducerReads(agent).worker_years_by_recipe()


class WorkerYears(unittest.TestCase):

    def test_the_sum_does_not_depend_on_the_order_the_producers_are_held_in(self):
        self.assertEqual(years_when_held_in("abcd"), years_when_held_in("dcba"))
