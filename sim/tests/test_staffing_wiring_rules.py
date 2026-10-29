"""The projects module's staffing methods with their collaborators replaced by recorders: closing what nobody watches,
reopening what is restaffed, restoring a shut work, and the standing-revenue figure that ignores hours sold."""

QUICK_TOPIC = True

import types
import unittest

from sim.ledger.api import PayEdge
from sim.projects import constants
from sim.reporting.api import RecordEvent
from sim.tests import module_harness, production_host, projects_host
from sim.workforce.api import SetWageHoursSold
from sim.refusal import facts_of


def _events(module):
    return [command for command in module_harness.sent(module) if isinstance(command, RecordEvent)]


def Closing(closed_keys):
    module = projects_host.build(concern_market=lambda: {"a": 123.45})
    module.recorded = []
    module.STAFFING_REMEDIES = ()
    module.concerns_to_close_for_staffing = lambda: ["a"] if closed_keys else []
    module._staffing_shortfalls = lambda held: {"craftsmen": 1.0}
    module.staffing_held_totals = lambda: {}
    module.review_ventures = lambda rules, year: [types.SimpleNamespace(entry_key=key) for key in closed_keys]
    module.record_staffing_closures = lambda count, shortfalls: module.recorded.append(count)
    module.staffing_shortfall_words = lambda shortfalls: "craftsmen"
    module.staffing_shut_count = lambda: len(closed_keys)
    return module


class ClosingUnstaffed(unittest.TestCase):

    def test_what_the_review_closes_is_returned_counted_and_logged_with_its_kind(self):
        game = Closing(["press", "mill"])
        self.assertEqual(game.close_unstaffed_ventures(100), ["press", "mill"])
        self.assertEqual(game.recorded, [2])
        event, = _events(game)
        self.assertEqual(event.kind, "concerns_closed_unstaffed")

    def test_when_nothing_closes_nothing_is_recorded_or_logged(self):
        game = Closing([])
        self.assertEqual(game.close_unstaffed_ventures(100), [])
        self.assertEqual((game.recorded, _events(game)), ([], []))


def Reopening(reopened):
    business = types.SimpleNamespace(review_reopening=lambda household, world: reopened)
    module = projects_host.build(legacy_projects=types.SimpleNamespace(business=business), legacy_household_actor=lambda: "household",
                                 actor_world=lambda: "world")
    module.recorded = []
    module.record_staffing_reopenings = module.recorded.append
    module.staffing_shut_count = lambda: 0
    return module


class ReopeningRestaffed(unittest.TestCase):

    def test_what_the_business_reopens_is_returned_counted_and_logged(self):
        game = Reopening(["press"])
        self.assertEqual(game.reopen_restaffed_ventures(100), ["press"])
        self.assertEqual(game.recorded, [1])
        self.assertEqual(_events(game)[0].kind, "concerns_reopened")

    def test_when_nothing_reopens_nothing_is_logged(self):
        game = Reopening([])
        self.assertEqual(game.reopen_restaffed_ventures(100), [])
        self.assertEqual(_events(game), [])


def Restoring(closure_age, fee=100.0, cash=1000.0):
    projects = types.SimpleNamespace(mothballed={"press"}, done={"press"}, business=types.SimpleNamespace(
        restore=lambda node_id: None, close_plant=lambda node_id: None))
    module = projects_host.build(
        legacy_projects=projects, tree={"press": {"pre": []}}, reopen_fee=lambda node_id: fee, spending_power=lambda kind: cash,
        acting_balance=cash, is_venture=lambda node_id: True, year=100)
    module.CLOSED_FOR_STAFF = "staff"
    module.running_gate_refusal = lambda node_id: None
    module.staff_closure_age = lambda node_id: closure_age
    return module


def _paid(module):
    return [command.amount for command in module_harness.sent(module) if isinstance(command, PayEdge)]


class RestoreWork(unittest.TestCase):

    def restore(self, **keywords):
        game = Restoring(**keywords)
        ok, line = game.restore_work("press")
        return game, ok, line

    def test_inside_the_grace_window_the_restoration_says_it_was_discounted_and_how_old_the_closure_was(self):
        game, ok, line = self.restore(closure_age=3)
        self.assertTrue(ok)
        self.assertTrue(facts_of(line)["discounted"])
        self.assertEqual(facts_of(line)["closure_age"], 3)
        self.assertEqual(_paid(game), [100.0])

    def test_after_the_window_it_says_it_was_not_discounted(self):
        _game, ok, line = self.restore(closure_age=constants.STAFF_CLOSURE_GRACE + 1)
        self.assertTrue(ok)
        self.assertFalse(facts_of(line)["discounted"])

    def test_a_work_not_shut_for_want_of_staff_has_no_closure_age(self):
        _game, ok, line = self.restore(closure_age=None)
        self.assertIsNone(facts_of(line)["closure_age"])

    def test_a_fee_beyond_what_can_be_raised_is_refused_and_nothing_is_paid(self):
        game, ok, _line = self.restore(closure_age=3, fee=5000.0, cash=1000.0)
        self.assertFalse(ok)
        self.assertEqual(_paid(game), [])

    def test_a_work_that_was_not_shut_is_refused(self):
        game = Restoring(closure_age=3)
        game.needs.legacy_projects().mothballed.clear()
        self.assertFalse(game.restore_work("press")[0])


class StandingRevenue:
    """The production module over a household whose hours sold on request are read and set as the workforce module would."""

    def __init__(self):
        self.hours = 700.0
        self.seen = []
        self.module = production_host.build(
            hour_commitments=lambda: {"wage_hours": self.hours},
            answers={SetWageHoursSold: lambda command: setattr(self, "hours", command.hours)})
        self.module.revenue = self.revenue

    def revenue(self):
        self.seen.append(self.hours)
        return 1000.0

    def revenue_capacity(self):
        return self.module.revenue_capacity()


class RevenueCapacity(unittest.TestCase):

    def test_revenue_is_read_as_if_no_hours_had_been_sold_this_year(self):
        game = StandingRevenue()
        self.assertEqual(game.revenue_capacity(), 1000.0)
        self.assertEqual(game.seen, [0.0])

    def test_the_hours_sold_are_put_back_afterwards(self):
        game = StandingRevenue()
        game.revenue_capacity()
        self.assertEqual(game.hours, 700.0)


if __name__ == "__main__":
    unittest.main()
