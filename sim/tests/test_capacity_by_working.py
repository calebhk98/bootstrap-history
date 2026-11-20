"""capacity_by_working: a producer's capacity moved toward what the runs it worked call for, and the share of its
workplaces that works when the price just covers a run's full cost."""

QUICK_TOPIC = True

import unittest

from sim.economy.capacity_by_working import capacity_toward_working, normal_share
from sim.economy.producers import COST_SPREAD_WITHIN_PRODUCER, share_working

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


class NormalShare(unittest.TestCase):
    SPREAD = COST_SPREAD_WITHIN_PRODUCER

    def test_without_plant_it_is_the_share_that_works_when_a_run_brings_in_what_it_costs(self):
        self.assertAlmostEqual(normal_share(40.0, 0.0, self.SPREAD), share_working(1.0, 1.0))

    def test_with_plant_it_is_the_share_that_works_when_the_price_covers_the_running_cost_and_the_charge(self):
        self.assertAlmostEqual(normal_share(40.0, 10.0, self.SPREAD), share_working(50.0, 40.0))

    def test_a_charge_on_plant_raises_it(self):
        self.assertGreater(normal_share(40.0, 10.0, self.SPREAD), normal_share(40.0, 0.0, self.SPREAD))
        self.assertGreater(normal_share(40.0, 20.0, self.SPREAD), normal_share(40.0, 10.0, self.SPREAD))

    def test_a_cost_or_a_charge_that_is_nothing_or_no_number_gives_the_share_without_plant(self):
        plain = normal_share(40.0, 0.0, self.SPREAD)
        for running, charge in ((0.0, 10.0), (float("inf"), 10.0), (float("nan"), 10.0), (40.0, float("nan")), (40.0, float("inf")), (40.0, -3.0)):
            self.assertEqual(normal_share(running, charge, self.SPREAD), plain)


if __name__ == "__main__":
    unittest.main()
