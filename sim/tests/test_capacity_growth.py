"""A producer whose runs pay grows toward the runs buyers call for, no faster than a year's change."""
QUICK_TOPIC = True

import unittest

from sim.economy.capacity_growth import grown_capacity


class GrownCapacityTest(unittest.TestCase):
    def test_grows_by_a_year_s_change_when_demand_is_far_above(self):
        self.assertAlmostEqual(grown_capacity(capacity=100.0, expected_runs=400.0, share_paying=1.0, step_share=0.25), 125.0)

    def test_stops_at_the_capacity_the_expected_runs_need(self):
        self.assertAlmostEqual(grown_capacity(100.0, 110.0, 1.0, 0.25), 110.0)

    def test_the_paying_share_raises_the_capacity_wanted(self):
        self.assertAlmostEqual(grown_capacity(100.0, 110.0, 0.5, 0.25), 125.0)

    def test_never_shrinks(self):
        self.assertEqual(grown_capacity(100.0, 20.0, 1.0, 0.25), 100.0)

    def test_nothing_grows_when_no_workplace_pays(self):
        self.assertEqual(grown_capacity(100.0, 400.0, 0.0, 0.25), 100.0)


if __name__ == "__main__":
    unittest.main()
