"""`ProducerReads.worker_years_by_recipe` sums in producer id order, whatever order the live economy holds them in."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace
from unittest import mock

from sim.markets import reads_producers
from sim.markets.reads_producers import ProducerReads

# runs chosen so the float sum depends on the order
RUNS = {"a": 1.0e16, "b": 1.0, "c": -1.0e16, "d": 1.0}
RECIPE = SimpleNamespace(labour_hours={"hand": 1.0})


def years_when_held_in(order):
    producers = {name: SimpleNamespace(agent_id=name, recipe_id="r", capacity_runs=RUNS[name]) for name in order}
    agent = SimpleNamespace(economy=lambda: "economy")
    with mock.patch.multiple(reads_producers.economy_api, producers_of=lambda economy: producers,
                             recipes_of=lambda economy: {"r": RECIPE}, working_hours_per_year=lambda economy: 1.0):
        return ProducerReads(agent).worker_years_by_recipe()


class WorkerYears(unittest.TestCase):

    def test_the_sum_does_not_depend_on_the_order_the_producers_are_held_in(self):
        self.assertEqual(years_when_held_in("abcd"), years_when_held_in("dcba"))
