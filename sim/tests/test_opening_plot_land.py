"""The opening's demand is sized on the plots its own land market leaves: a cohort's plot takes no more land than it
kept after the last opening's land market. Each test calls one function on written-out inputs."""
QUICK_TOPIC = True

import unittest

from sim.economy import opening_own


class PlotLandTests(unittest.TestCase):
    def test_before_any_opening_a_plot_may_take_all_the_cohort_holds(self):
        self.assertEqual(opening_own.plot_land({"a": 10.0, "b": 4.0}, None), {"a": 10.0, "b": 4.0})

    def test_a_plot_takes_no_more_than_it_kept_after_the_last_land_market(self):
        # producers outbid the plots of `a` for all its land and of `b` for half
        self.assertEqual(opening_own.plot_land({"a": 10.0, "b": 4.0}, {"a": 0.0, "b": 2.0}), {"a": 0.0, "b": 2.0})

    def test_a_plot_never_takes_more_than_the_cohort_holds(self):
        self.assertEqual(opening_own.plot_land({"a": 10.0}, {"a": 12.0}), {"a": 10.0})

    def test_a_cohort_the_last_opening_did_not_have_keeps_what_it_holds(self):
        self.assertEqual(opening_own.plot_land({"a": 10.0, "new": 3.0}, {"a": 6.0}), {"a": 6.0, "new": 3.0})


if __name__ == "__main__":
    unittest.main()
