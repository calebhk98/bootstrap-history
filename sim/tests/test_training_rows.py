"""Training rows are one named record (TrainingRow): the rules that read them take people and a ready year by name,
and people bought and still learning (trade None) are told apart from a trade being taught. Each rule is called on
rows written out here (sweep 2, N1, N2, N5)."""
QUICK_TOPIC = True

import unittest

from sim.labour.staff_book import StaffBook
from sim.labour.staff_moves import apprentices_of, dismiss
from sim.labour.trade_first_hands import cohort_rows
from sim.workforce.api import TrainingRow


class Cohorts(unittest.TestCase):
    def test_a_cohort_with_no_covered_task_is_one_row_of_the_trade_ready_at_the_end(self):
        self.assertEqual(cohort_rows(100, "machinist", 3.0, 4.0, 8.0, 1.0), [TrainingRow("machinist", 3.0, 104)])

    def test_a_covered_share_is_an_early_row_and_the_rest_a_late_one(self):
        early, late = cohort_rows(100, "machinist", 4.0, 4.0, 8.0, 0.5)
        self.assertEqual((early.trade, late.trade, early.people + late.people), ("machinist", "machinist", 4.0))
        self.assertLess(early.ready_year, late.ready_year)


class Moves(unittest.TestCase):
    ROWS = [TrainingRow(None, 5.0, 103), TrainingRow("smith", 2.0, 102), TrainingRow("mason", 1.0, 102)]

    def test_apprentices_of_counts_the_trade_and_never_the_people_bought(self):
        self.assertEqual(apprentices_of(self.ROWS, "smith"), 2.0)
        self.assertEqual(apprentices_of(self.ROWS, None), 5.0)    # the bought row is the trade-less one; callers name a trade

    def test_dismissing_stops_apprentices_of_that_trade_only_and_keeps_the_bought_row(self):
        _gone, _left, stopped, still, unmet = dismiss(0.0, self.ROWS, "smith", 2.0)
        self.assertEqual((stopped, unmet), (2.0, 0.0))
        self.assertEqual(still, [TrainingRow(None, 5.0, 103), TrainingRow("mason", 1.0, 102)])
        self.assertEqual(self.ROWS[1].people, 2.0)       # the given rows are not edited


class Book(unittest.TestCase):
    def book(self, rows):
        from types import SimpleNamespace
        return StaffBook(SimpleNamespace(workforce=SimpleNamespace(training=rows)))

    def test_in_training_total_is_people_being_taught_a_trade_not_people_bought(self):
        self.assertEqual(self.book(Moves.ROWS).in_training_total(), 3.0)


if __name__ == "__main__":
    unittest.main()
