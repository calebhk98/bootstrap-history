"""Complaints 91 and 640: the step reply carries the automation rows of the years just played and not an older year's.
`rows_of_years_stepped` is called on rows written out here; the audit window itself is test_ui_step_automation_line."""
QUICK_TOPIC = True

import unittest

from sim.ui.proto.step_automation import rows_of_years_stepped

ROWS = [{"year": 99, "what": "old"}, {"year": 100, "what": "last"}, {"year": 101, "what": "now"}]


class StepAutomationRows(unittest.TestCase):
    def test_a_row_from_the_year_just_played_is_kept(self):
        self.assertEqual([row["what"] for row in rows_of_years_stepped(ROWS, 101)], ["now"])

    def test_an_older_years_row_is_not_repeated(self):
        self.assertNotIn("old", [row["what"] for row in rows_of_years_stepped(ROWS, 100)])

    def test_a_many_year_step_keeps_every_year_it_played_oldest_first(self):
        self.assertEqual([row["what"] for row in rows_of_years_stepped(ROWS, 99)], ["old", "last", "now"])

    def test_no_rows_give_none(self):
        self.assertEqual(rows_of_years_stepped([], 100), [])


if __name__ == "__main__":
    unittest.main()
