"""Idle runs a producer could still add, which entry counts as supply already in the market: land it was not granted is not idle capacity."""
QUICK_TOPIC = True

import unittest

from sim.economy.entry_spare import idle_runs


class IdleRunsTest(unittest.TestCase):
    def test_capacity_not_worked_is_idle(self):
        self.assertEqual(idle_runs(capacity_runs=100.0, last_runs=30.0, pending_runs=0.0, land_run_cap=-1.0), 70.0)

    def test_land_cap_below_capacity_bounds_the_idle_runs(self):
        self.assertEqual(idle_runs(capacity_runs=100.0, last_runs=30.0, pending_runs=0.0, land_run_cap=40.0), 10.0)

    def test_a_producer_working_all_the_land_it_was_granted_has_none_idle(self):
        self.assertEqual(idle_runs(capacity_runs=100.0, last_runs=40.0, pending_runs=0.0, land_run_cap=40.0), 0.0)
        self.assertEqual(idle_runs(capacity_runs=100.0, last_runs=40.0, pending_runs=0.0, land_run_cap=0.0), 0.0)

    def test_plant_on_the_way_counts_when_land_allows(self):
        self.assertEqual(idle_runs(capacity_runs=100.0, last_runs=100.0, pending_runs=20.0, land_run_cap=-1.0), 20.0)

    def test_a_producer_that_never_ran_has_all_its_capacity_idle(self):
        self.assertEqual(idle_runs(capacity_runs=100.0, last_runs=-1.0, pending_runs=0.0, land_run_cap=-1.0), 100.0)


if __name__ == "__main__":
    unittest.main()
