"""capacity_by_working.capacity_toward_working: a producer's capacity moved toward what the runs it worked call for."""

QUICK_TOPIC = True

import unittest

from sim.economy.capacity_by_working import capacity_toward_working

NORMAL_SHARE = 0.5      # half the workplaces work when a run brings in what it costs, in these cases


class CapacityTowardWorking(unittest.TestCase):
    def test_a_producer_working_the_normal_share_keeps_its_capacity(self):
        self.assertAlmostEqual(capacity_toward_working(100.0, 50.0, NORMAL_SHARE, 0.2, 0.25), 100.0)

    def test_working_more_than_the_normal_share_adds_a_share_of_the_gap(self):
        # 60 runs call for 60 / 0.5 = 120 of capacity; a fifth of the gap of 20 is 4
        self.assertAlmostEqual(capacity_toward_working(100.0, 60.0, NORMAL_SHARE, 0.2, 0.25), 100.0 + 0.2 * (120.0 - 100.0))

    def test_working_less_takes_the_same_share_of_the_gap_away(self):
        # 40 runs call for 80: the gap is the same 20 the other way
        self.assertAlmostEqual(capacity_toward_working(100.0, 40.0, NORMAL_SHARE, 0.2, 0.25), 100.0 - 0.2 * (100.0 - 80.0))

    def test_a_year_adds_no_more_than_the_most_change(self):
        # 400 runs call for 800; a fifth of the gap of 700 is 140, held to a quarter of the capacity
        self.assertAlmostEqual(capacity_toward_working(100.0, 400.0, NORMAL_SHARE, 0.2, 0.25), 125.0)

    def test_a_year_takes_no_more_than_the_most_change(self):
        # no runs call for none; the whole gap closed in a year (share one) is held to a quarter
        self.assertAlmostEqual(capacity_toward_working(100.0, 0.0, NORMAL_SHARE, 1.0, 0.25), 75.0)

    def test_a_producer_that_worked_nothing_loses_the_share_of_its_capacity(self):
        self.assertAlmostEqual(capacity_toward_working(100.0, 0.0, NORMAL_SHARE, 0.2, 0.25), 80.0)

    def test_repeated_years_at_the_same_runs_come_to_the_capacity_they_call_for(self):
        capacity = 100.0
        for _year in range(200):
            capacity = capacity_toward_working(capacity, 60.0, NORMAL_SHARE, 0.2, 0.25)
        self.assertAlmostEqual(capacity, 120.0, places=6)

    def test_the_capacity_reached_does_not_depend_on_where_it_started(self):
        ends = []
        for start in (20.0, 100.0, 900.0):
            capacity = start
            for _year in range(300):
                capacity = capacity_toward_working(capacity, 60.0, NORMAL_SHARE, 0.2, 0.25)
            ends.append(capacity)
        self.assertAlmostEqual(ends[0], ends[1], places=6)
        self.assertAlmostEqual(ends[1], ends[2], places=6)

    def test_no_normal_share_leaves_the_capacity_as_it_is(self):
        self.assertAlmostEqual(capacity_toward_working(100.0, 60.0, 0.0, 0.2, 0.25), 100.0)


if __name__ == "__main__":
    unittest.main()
