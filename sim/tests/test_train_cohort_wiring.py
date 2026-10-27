"""Complaint 644: `TrainingMixin.train` writes the cohort into the household's training list as the rows `cohort_rows` gives
(an early slice and the rest), pays the fee, spends the teacher's hours and presses the source trade. Called on a stand-in
`self` carrying what it reads; the rows and the stall window are test_trade_first_hands."""
QUICK_TOPIC = True

import types
import unittest
from sim.tests import workforce_stand_in

from sim.labour.labour_training import TrainingMixin
from sim.labour.trade_first_hands import cohort_rows

YEAR = 100
HOURS_PER_PERSON_YEAR = 2000.0
PLAN = {"count": 2.0, "from": "smith", "hours": 300.0, "fee": 40.0, "years": 4.0, "teacher": None, "uncovered": 0.5}


class Teacher(TrainingMixin):
    """The parts of a labour market and a world that `train` reads and writes."""

    def __init__(self, plan=PLAN, refusal=None):
        self.plan, self.refusal = plan, refusal
        self.paid, self.pressed = [], []
        self.household = types.SimpleNamespace(training=[], trades_created=set(), teaching_hours_this_year=None)
        self._world = types.SimpleNamespace(
            workforce=self.household, view=workforce_stand_in.view_of(self.household), year=YEAR, state=types.SimpleNamespace(household=self.household, scenario=types.SimpleNamespace(year=YEAR)),
            send=lambda command: self.paid.append((command.amount, command.purpose)), EDGE_WORKERS="workers",
            HOURS_PER_PERSON_YEAR=HOURS_PER_PERSON_YEAR,
            plain_number=lambda number: str(number), money_text=lambda money, grouped=False: str(money))
        self.labour_market = types.SimpleNamespace(press=lambda trade, hours: self.pressed.append((trade, hours)))

    def train_check(self, trade, count, frm=None):
        return (None, self.refusal) if self.refusal else (self.plan, None)

    def _full_years(self, trade):
        return 8.0

    def director_pool(self):
        return 1000.0

    def director_hours_committed(self):
        return 400.0


class TrainTests(unittest.TestCase):
    def test_the_cohort_is_written_as_the_rows_cohort_rows_gives(self):
        game = Teacher()
        trained, _text = game.train("machinist", 2)
        self.assertTrue(trained)
        self.assertEqual(game.household.training, cohort_rows(YEAR, "machinist", 2.0, 4.0, 8.0, 0.5))
        self.assertEqual(len(game.household.training), 2)

    def test_the_fee_is_paid_the_hours_booked_the_trade_created_and_the_source_pressed(self):
        game = Teacher()
        game.train("machinist", 2)
        self.assertEqual([money for money, _text in game.paid], [40.0])
        self.assertEqual(game.household.teaching_hours_this_year, 300.0)
        self.assertEqual(game.household.trades_created, {"machinist"})
        self.assertEqual(game.pressed, [("smith", 2.0 * HOURS_PER_PERSON_YEAR)])

    def test_a_refused_plan_changes_nothing(self):
        game = Teacher(refusal="refused")
        trained, refusal = game.train("machinist", 2)
        self.assertFalse(trained)
        self.assertEqual(refusal, "refused")
        self.assertEqual((game.household.training, game.paid, game.pressed), ([], [], []))


if __name__ == "__main__":
    unittest.main()
