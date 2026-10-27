"""Mod code can charge overhead against the directed-hours pool (Complaint 633): the hours count as committed.

The sum of the providers' answers is a function of the answers, the mod door records its provider as an operation, and the
committed-hours rule is read off the capacity mixin over a stand-in world."""
QUICK_TOPIC = True

import types
import unittest
from sim.tests import workforce_stand_in

from sim.engine import mod_code
from sim.labour.labour_capacity import CapacityMixin
from sim.tests import harness  # noqa: F401  (isolates the home directory)
from sim.workforce.provided import overhead_hours
from sim.tests.ui_stand_in import Game

POOL_HOURS = 2000.0


def labour(overhead_hours):
    household = types.SimpleNamespace(wage_hours_this_year=100.0, teaching_hours_this_year=10.0,
                                      relocation_hours_this_year=20.0, supervision_hours_this_year=30.0,
                                      bondage_years_left=0, directors_extra=0.0)
    world = types.SimpleNamespace(household=household, director_overhead_hours=lambda: overhead_hours,
                                  cfg={"founder_hours_per_year": POOL_HOURS, "director_hours_per_year": 0.0},
                                  founder_alive=True, workforce=household, view=workforce_stand_in.view_of(household), state=types.SimpleNamespace(household=household),
                                  simulation=lambda: Game(bondage_years_left=0))
    stub = types.SimpleNamespace(_world=world, BONDAGE_HOURS_SHARE=0.25)
    stub.director_pool = lambda: CapacityMixin.director_pool(stub)
    stub.director_hours_committed = lambda: CapacityMixin.director_hours_committed(stub)
    return stub


class DirectorOverhead(unittest.TestCase):
    def test_free_hours_fall_by_exactly_the_overhead(self):
        plain, charged = labour(0.0), labour(120.0)
        self.assertEqual(charged.director_pool(), plain.director_pool())
        self.assertEqual(charged.director_hours_committed() - plain.director_hours_committed(), 120.0)
        self.assertEqual((plain.director_pool() - plain.director_hours_committed())
                         - (charged.director_pool() - charged.director_hours_committed()), 120.0)

    def test_nothing_provided_charges_nothing(self):
        self.assertEqual(overhead_hours([]), 0.0)

    def test_provided_overheads_sum_and_a_negative_one_counts_as_zero(self):
        self.assertEqual(overhead_hours([120.0, 30.0, -50.0]), 150.0)

    def test_the_mod_door_records_the_function_as_an_answer_to_the_point(self):
        api = mod_code.ModCodeApi("test_overhead_k3f9")
        function = api.director_overhead(lambda sim: 120.0)
        self.assertEqual(api.operations.provided["director_overhead"], (function,))


if __name__ == "__main__":
    unittest.main()
