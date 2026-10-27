"""Mod code can charge overhead against the directed-hours pool (Complaint 633): the hours count as committed.

The registry is called with a stand-in sim, and the committed-hours rule is read off the capacity mixin over a stand-in world."""
QUICK_TOPIC = True

import types
import unittest
from sim.tests import workforce_stand_in

from sim.engine import director_overhead, mod_code
from sim.labour.labour_capacity import CapacityMixin
from sim.tests import harness  # noqa: F401  (isolates the home directory)

POOL_HOURS = 2000.0


def labour(overhead_hours):
    household = types.SimpleNamespace(wage_hours_this_year=100.0, teaching_hours_this_year=10.0,
                                      relocation_hours_this_year=20.0, supervision_hours_this_year=30.0,
                                      bondage_years_left=0, directors_extra=0.0)
    world = types.SimpleNamespace(household=household, director_overhead_hours=lambda: overhead_hours,
                                  cfg={"founder_hours_per_year": POOL_HOURS, "director_hours_per_year": 0.0},
                                  founder_alive=True, workforce=household, view=workforce_stand_in.view_of(household), state=types.SimpleNamespace(household=household))
    stub = types.SimpleNamespace(_world=world, BONDAGE_HOURS_SHARE=0.25)
    stub.director_pool = lambda: CapacityMixin.director_pool(stub)
    stub.director_hours_committed = lambda: CapacityMixin.director_hours_committed(stub)
    return stub


class DirectorOverhead(unittest.TestCase):
    def tearDown(self):
        director_overhead.OVERHEADS.clear()

    def test_free_hours_fall_by_exactly_the_overhead(self):
        plain, charged = labour(0.0), labour(120.0)
        self.assertEqual(charged.director_pool(), plain.director_pool())
        self.assertEqual(charged.director_hours_committed() - plain.director_hours_committed(), 120.0)
        self.assertEqual((plain.director_pool() - plain.director_hours_committed())
                         - (charged.director_pool() - charged.director_hours_committed()), 120.0)

    def test_nothing_registered_charges_nothing(self):
        self.assertEqual(director_overhead.total_hours(object()), 0.0)

    def test_registered_overheads_sum_and_a_negative_one_counts_as_zero(self):
        api = mod_code.ModCodeApi("test_overhead_k3f9")
        api.director_overhead(lambda sim: 120.0)
        api.director_overhead(lambda sim: sim.extra)
        api.director_overhead(lambda sim: -50.0)
        self.assertEqual(director_overhead.total_hours(types.SimpleNamespace(extra=30.0)), 150.0)


if __name__ == "__main__":
    unittest.main()
