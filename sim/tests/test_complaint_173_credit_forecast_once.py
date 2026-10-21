"""Complaint 173: the credit forecast block that `start` prints is shown in full once per game year; later starts that
year show a one-line summary on screen, and the figures stay in the JSON reply. The rule is
sim/ui/proto/credit_forecast.py, called on built replies; the screen is `render_start`. (A real run of starts:
test_scenarios_batch3_saves.)"""
QUICK_TOPIC = True

import copy
import unittest

from sim.ui.proto import credit_forecast
from sim.ui.proto.render_screens_start import render_start

YEAR = 100


def reply():
    return {"ok": True, "started": "tr_lateen_sail", "of_which_instalments_still_owed": 12.0,
            "on_credit": {"you_would_borrow": 400.0, "interest_rate_percent": 6.0, "estimated_annual_interest": 24.0,
                          "nothing_is_borrowed_yet": "nothing is borrowed yet",
                          "what_happens_there": "past that limit the lender stops"},
            "total_committed_across_active_work": {"you_have_promised": 900.0, "across_projects_in_hand": 3,
                                                   "your_real_ceiling_if_it_comes_to_that": 2000.0,
                                                   "what_this_means": "the whole of the country above"}}


class ShortenTests(unittest.TestCase):
    def test_the_first_showing_in_a_year_keeps_all_the_prose(self):
        out, said = reply(), {}
        self.assertTrue(credit_forecast.shorten(out, said, YEAR, False))
        self.assertEqual({key: value for key, value in out.items() if key != "credit_forecast_in_full"}, reply())
        self.assertTrue(out["credit_forecast_in_full"])
        self.assertEqual(said["credit_forecast"], YEAR)

    def test_a_later_start_the_same_year_keeps_the_figures_and_loses_the_prose(self):
        out, said = reply(), {"credit_forecast": YEAR}
        self.assertFalse(credit_forecast.shorten(out, said, YEAR, False))
        self.assertEqual(out["on_credit"]["you_would_borrow"], 400.0)
        self.assertEqual(out["total_committed_across_active_work"]["you_have_promised"], 900.0)
        for block, prose_keys in credit_forecast.CREDIT_PROSE.items():
            for prose_key in prose_keys:
                self.assertNotIn(prose_key, out[block])
        self.assertIs(out["credit_forecast_in_full"], False)

    def test_full_asks_for_the_whole_block_again(self):
        out, said = reply(), {"credit_forecast": YEAR}
        self.assertTrue(credit_forecast.shorten(out, said, YEAR, True))
        self.assertIn("what_happens_there", out["on_credit"])

    def test_a_new_year_shows_the_full_block_again(self):
        out, said = reply(), {"credit_forecast": YEAR}
        self.assertTrue(credit_forecast.shorten(out, said, YEAR + 1, False))
        self.assertIn("what_happens_there", out["on_credit"])
        self.assertEqual(said["credit_forecast"], YEAR + 1)

    def test_a_short_showing_does_not_move_the_year_said(self):
        said = {"credit_forecast": YEAR}
        credit_forecast.shorten(reply(), said, YEAR, False)
        self.assertEqual(said, {"credit_forecast": YEAR})

    def test_a_reply_with_no_credit_block_is_left_alone(self):
        out = {"ok": True, "started": "x"}
        self.assertIsNone(credit_forecast.shorten(out, {}, YEAR, False))
        self.assertEqual(out, {"ok": True, "started": "x"})

    def test_one_block_alone_is_shortened_too(self):
        out = {"ok": True, "on_credit": {"you_would_borrow": 5.0, "what_happens_there": "x"}}
        credit_forecast.shorten(out, {"credit_forecast": YEAR}, YEAR, False)
        self.assertEqual(out["on_credit"], {"you_would_borrow": 5.0})


class ScreenTests(unittest.TestCase):
    @staticmethod
    def shortened():
        out = reply()
        credit_forecast.shorten(out, {"credit_forecast": YEAR}, YEAR, False)
        return out

    def test_the_first_credit_start_prints_the_full_forecast_prose(self):
        # presentation: the explanation is on screen
        full = reply()
        credit_forecast.shorten(full, {}, YEAR, False)
        self.assertIn("past that limit", render_start(full))

    def test_a_later_start_prints_a_one_line_summary_not_the_prose(self):
        # presentation: the short form on screen
        text = render_start(self.shortened())
        self.assertNotIn("past that limit", text)
        self.assertNotIn("the whole of the country above", text)
        credit_lines = [line for line in text.splitlines() if line.startswith("credit:")]
        self.assertEqual(len(credit_lines), 1)
        self.assertIn("would borrow 400", credit_lines[0])
        self.assertIn("900 promised across 3 projects", credit_lines[0])

    def test_the_figures_stay_in_the_reply_the_screen_was_drawn_from(self):
        out = self.shortened()
        before = copy.deepcopy(out)
        render_start(out)
        self.assertEqual(out, before)


if __name__ == "__main__":
    unittest.main()
