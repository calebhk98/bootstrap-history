"""Complaint 144: wage work sold on request is kept in the household's books: what is sold this year, a log line of kind
`wage_work_sold`, last year's summary once the year closes, and a `preview` that changes nothing. The `work` command passes the
wage of one call to its reply. Each method is called on a stand-in; the money text and the remedy are test_wage_work_ledger."""
QUICK_TOPIC = True

import types
import unittest
from sim.tests import workforce_stand_in

from sim.refusal import cause_of, facts_of
from sim.labour.labour_wage_ledger import WageLedgerMixin
from sim.ui.proto.dispatch_labour import _cmd_work
from sim.tests import event_stand_in
from sim.tests.ui_stand_in import StandIn
from sim.workforce.api import WorkForWages


def household(**fields):
    books = dict(wage_hours_this_year=0.0, wage_income_this_year=0.0, wages_earned=0.0, wage_work_last_year=None, log=[], capital=100.0)
    books.update(fields)
    return types.SimpleNamespace(**books)


class Books(WageLedgerMixin):
    """The household's books and the little of the world the ledger reads."""

    def __init__(self, held=None, year=100):
        self.held = held or household()
        self._world = workforce_stand_in.World(
            workforce=self.held, view=workforce_stand_in.view_of(self.held), year=year,
            state=types.SimpleNamespace(household=self.held, scenario=types.SimpleNamespace(year=year)),
            plain_number=lambda number: "%g" % number, money_text=lambda money, grouped=False, short=False: "%g" % money,
            logged_events=lambda: len(self.held.log))
        event_stand_in.stood_in(self._world)

    def work_for_wages(self, trade, hours):
        self.held.capital += 30.0
        self.held.wage_hours_this_year += hours
        self.held.wage_income_this_year += 30.0
        self.held.wages_earned += 30.0
        self.held.log.append((100, "sold"))
        return 30.0, None


class ThisYearsWageWork(unittest.TestCase):
    def test_no_hours_sold_gives_an_empty_summary(self):
        self.assertEqual(Books().wage_work_this_year(), {})

    def test_the_summary_is_the_hours_sold_and_the_wage_income_and_nothing_displaced(self):
        summary = Books(household(wage_hours_this_year=1500.0, wage_income_this_year=312.46)).wage_work_this_year()
        self.assertEqual(summary, {"hours": 1500.0, "wage_income": 312.5})

    def test_a_sale_is_logged_as_wage_work_sold_with_its_trade_hours_and_pay(self):
        books = Books()
        books.log_wage_work("scholar", 1500, 312.0)
        year, line = books.held.log[0]
        self.assertEqual((year, cause_of(line)), (100, "wage_work_sold"))
        self.assertEqual(facts_of(line), {"trade": "scholar", "hours": 1500, "pay": 312.0})


class ClosingTheYear(unittest.TestCase):
    def test_this_years_books_become_last_years_with_the_year_and_are_cleared(self):
        books = Books(household(wage_hours_this_year=1000.0, wage_income_this_year=200.0), year=101)
        books.close_wage_year()
        self.assertEqual(books.held.wage_work_last_year, {"hours": 1000.0, "wage_income": 200.0, "year": 101})
        self.assertEqual((books.held.wage_hours_this_year, books.held.wage_income_this_year), (0.0, 0.0))

    def test_a_year_with_no_wage_work_leaves_no_summary(self):
        books = Books(household(wage_work_last_year={"hours": 5.0}))
        books.close_wage_year()
        self.assertIsNone(books.held.wage_work_last_year)


class DryRun(unittest.TestCase):
    def test_the_dry_run_asks_for_a_quote_and_returns_its_pay_and_note(self):
        asked = []
        books = Books()
        books.work_for_wages = lambda trade, hours, commit=True: asked.append((trade, hours, commit)) or (30.0, "note")
        self.assertEqual(books.work_for_wages_dry_run("scholar", 1500), (30.0, "note"))
        self.assertEqual(asked, [("scholar", 1500, False)])


class WorkCommand(unittest.TestCase):
    def game(self):
        return StandIn(answers={WorkForWages: (312.46, None)}, work_for_wages_dry_run=lambda trade, hours: (312.46, None),
                       hours_available={"director_pool": 2000.0, "director_committed": 500.0}, acting_balance=900.0)

    def test_a_preview_states_the_wage_and_says_nothing_changed(self):
        reply = _cmd_work(self.game(), {}, {"cmd": "work", "trade": "scholar", "hours": 1500, "preview": True}, None)
        self.assertTrue(reply["preview"] and reply["nothing_changed"])
        self.assertEqual(reply["earned"], 312.5)

    def test_the_work_reports_the_same_wage_the_preview_did(self):
        game = self.game()
        preview = _cmd_work(game, {}, {"cmd": "work", "trade": "scholar", "hours": 1500, "preview": True}, None)
        done = _cmd_work(game, {}, {"cmd": "work", "trade": "scholar", "hours": 1500}, None)
        self.assertEqual(done["earned"], preview["earned"])
        self.assertNotIn("preview", done)

    def test_a_refused_sale_is_not_ok_and_earns_nothing(self):
        game = self.game()
        game.answers[WorkForWages] = (0.0, "hours must be greater than zero")
        reply = _cmd_work(game, {}, {"cmd": "work", "trade": "scholar", "hours": 0}, None)
        self.assertIs(reply["ok"], False)


if __name__ == "__main__":
    unittest.main()
