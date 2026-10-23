"""Complaint 640: `start` says at the time when a project wants more hours of a trade a year than the society can call on.
`trades_beyond_ceiling` is called on wants and ceilings written out here: the yearly share is the total over the project's
calendar years (never more than the total), and only a trade whose ceiling is below its share is listed."""
QUICK_TOPIC = True

import unittest

from sim.ui.proto.staffing_ceiling import trades_beyond_ceiling

CEILINGS = {"scribe": 100.0, "smith": 5000.0, "scholar": -20.0}


class TradesBeyondCeiling(unittest.TestCase):
    def beyond(self, wants, years):
        return trades_beyond_ceiling(wants, years, CEILINGS.__getitem__)

    def test_a_trade_wanting_more_a_year_than_the_ceiling_is_listed_with_both_figures(self):
        self.assertEqual(self.beyond({"scribe": 1000.0}, 4.0), [("scribe", 250.0, 100.0)])

    def test_a_trade_the_ceiling_covers_is_not_listed(self):
        self.assertEqual(self.beyond({"smith": 1000.0}, 4.0), [])

    def test_a_ceiling_exactly_at_the_need_is_not_beyond(self):
        self.assertEqual(self.beyond({"scribe": 400.0}, 4.0), [])

    def test_a_project_shorter_than_a_year_wants_its_whole_total_in_the_year(self):
        self.assertEqual(self.beyond({"scribe": 300.0}, 0.5), [("scribe", 300.0, 100.0)])

    def test_a_trade_the_society_has_none_of_shows_a_ceiling_of_zero_not_a_negative(self):
        self.assertEqual(self.beyond({"scholar": 40.0}, 1.0), [("scholar", 40.0, 0.0)])

    def test_a_trade_with_no_hours_wanted_is_never_listed(self):
        self.assertEqual(self.beyond({"scholar": 0.0}, 1.0), [])

    def test_a_project_that_wants_no_trades_lists_none(self):
        self.assertEqual(trades_beyond_ceiling(None, 3.0, CEILINGS.__getitem__), [])


if __name__ == "__main__":
    unittest.main()
