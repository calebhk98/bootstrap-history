"""StaffingMixin methods on stand-in games with their collaborators replaced by recorders: closing what nobody
watches, reopening what is restaffed, restoring a shut work, and the standing-revenue figure that ignores hours sold."""

QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.engine import projects_staffing
from sim.engine.economy_production import ProductionMixin
from sim.engine.projects_staffing import StaffingMixin
from sim.refusal import cause_of, facts_of
from sim.tests import event_stand_in


class Closing(StaffingMixin):
    send = event_stand_in.send

    def __init__(self, closed_keys):
        self.state = types.SimpleNamespace(household=types.SimpleNamespace(log=[]))
        self.keys = closed_keys
        self.recorded = []
        self.labour = types.SimpleNamespace(yearly_value_of=lambda planned: 123.45)
        self.STAFFING_REMEDIES = ()

    def concerns_to_close_for_staffing(self):
        return ["a"] if self.keys else []

    def _staffing_shortfalls(self, held):
        return {"craftsmen": 1.0}

    def staffing_held_totals(self):
        return {}

    def review_ventures(self, rules, year):
        return [types.SimpleNamespace(entry_key=key) for key in self.keys]

    def record_staffing_closures(self, count, shortfalls):
        self.recorded.append(count)

    def staffing_shortfall_words(self, shortfalls):
        return "craftsmen"

    def staffing_shut_count(self):
        return len(self.keys)


class ClosingUnstaffed(unittest.TestCase):

    def test_what_the_review_closes_is_returned_counted_and_logged_with_its_kind(self):
        game = Closing(["press", "mill"])
        self.assertEqual(game.close_unstaffed_ventures(100), ["press", "mill"])
        self.assertEqual(game.recorded, [2])
        (_year, line), = game.state.household.log
        self.assertEqual(cause_of(line), "concerns_closed_unstaffed")

    def test_when_nothing_closes_nothing_is_recorded_or_logged(self):
        game = Closing([])
        self.assertEqual(game.close_unstaffed_ventures(100), [])
        self.assertEqual((game.recorded, game.state.household.log), ([], []))


class Reopening(StaffingMixin):
    send = event_stand_in.send

    def __init__(self, reopened):
        business = types.SimpleNamespace(review_reopening=lambda household, world: reopened)
        self.state = types.SimpleNamespace(household=types.SimpleNamespace(log=[]), projects=types.SimpleNamespace(business=business))
        self.household = self.state.household
        self.recorded = []

    def view(self, name):
        return lambda: None

    def record_staffing_reopenings(self, count):
        self.recorded.append(count)

    def staffing_shut_count(self):
        return 0


class ReopeningRestaffed(unittest.TestCase):

    def test_what_the_business_reopens_is_returned_counted_and_logged(self):
        game = Reopening(["press"])
        self.assertEqual(game.reopen_restaffed_ventures(100), ["press"])
        self.assertEqual(game.recorded, [1])
        self.assertEqual(cause_of(game.state.household.log[0][1]), "concerns_reopened")

    def test_when_nothing_reopens_nothing_is_logged(self):
        game = Reopening([])
        self.assertEqual(game.reopen_restaffed_ventures(100), [])
        self.assertEqual(game.state.household.log, [])


class Restoring(StaffingMixin):
    STAFF_CLOSURE_GRACE = 5

    def __init__(self, closure_age, fee=100.0, cash=1000.0):
        projects = types.SimpleNamespace(mothballed={"press"}, done={"press"}, business=types.SimpleNamespace(
            restore=lambda node_id: None, close_plant=lambda node_id: None))
        self.state = types.SimpleNamespace(projects=projects, household=types.SimpleNamespace(capital=cash),
                                           scenario=types.SimpleNamespace(year=100))
        self.nodes = {"press": {"pre": []}}
        self.age, self.fee, self.cash = closure_age, fee, cash
        self.paid = []
        self.sent = []

    def send(self, command):
        self.sent.append(command)

    def running_gate_refusal(self, node_id):
        return None

    def reopen_fee(self, node_id, units):
        return self.fee

    def reopen_units(self, node_id):
        return 1

    def staff_closure_age(self, node_id):
        return self.age

    def spending_power(self, kind):
        return self.cash

    def pay_edge(self, edge, fee, text):
        self.paid.append(fee)

    def is_venture(self, node_id):
        return True


class RestoreWork(unittest.TestCase):

    def restore(self, **keywords):
        game = Restoring(**keywords)
        with mock.patch.object(projects_staffing.cause_book, "record_concern", lambda *args: None):
            ok, line = game.restore_work("press")
        return game, ok, line

    def test_inside_the_grace_window_the_restoration_says_it_was_discounted_and_how_old_the_closure_was(self):
        game, ok, line = self.restore(closure_age=3)
        self.assertTrue(ok)
        self.assertTrue(facts_of(line)["discounted"])
        self.assertEqual(facts_of(line)["closure_age"], 3)
        self.assertEqual(game.paid, [100.0])

    def test_after_the_window_it_says_it_was_not_discounted(self):
        _game, ok, line = self.restore(closure_age=6)
        self.assertTrue(ok)
        self.assertFalse(facts_of(line)["discounted"])

    def test_a_work_not_shut_for_want_of_staff_has_no_closure_age(self):
        _game, ok, line = self.restore(closure_age=None)
        self.assertIsNone(facts_of(line)["closure_age"])

    def test_a_fee_beyond_what_can_be_raised_is_refused_and_nothing_is_paid(self):
        game, ok, _line = self.restore(closure_age=3, fee=5000.0, cash=1000.0)
        self.assertFalse(ok)
        self.assertEqual(game.paid, [])

    def test_a_work_that_was_not_shut_is_refused(self):
        game = Restoring(closure_age=3)
        game.state.projects.mothballed.clear()
        self.assertFalse(game.restore_work("press")[0])


class StandingRevenue(ProductionMixin):
    def __init__(self):
        self.state = types.SimpleNamespace(household=types.SimpleNamespace(wage_hours_this_year=700.0))
        self.seen = []

    def revenue(self):
        self.seen.append(self.state.household.wage_hours_this_year)
        return 1000.0


class RevenueCapacity(unittest.TestCase):

    def test_revenue_is_read_as_if_no_hours_had_been_sold_this_year(self):
        game = StandingRevenue()
        self.assertEqual(game.revenue_capacity(), 1000.0)
        self.assertEqual(game.seen, [0.0])

    def test_the_hours_sold_are_put_back_afterwards(self):
        game = StandingRevenue()
        game.revenue_capacity()
        self.assertEqual(game.state.household.wage_hours_this_year, 700.0)


if __name__ == "__main__":
    unittest.main()
