"""A household that cannot meet its payroll loses staff, dearest trade first, and the loss is logged with its count
(`Workforce.shed_unpayable_staff`, called by the staff phase). The game is a stand-in carrying the labour calls the rule makes."""
QUICK_TOPIC = True

import types
import unittest
from sim.tests import workforce_stand_in

from sim.refusal import cause_of, facts_of
from sim.tests.workforce_host import workforce_over

WAGE_PER_YEAR = {"smith": 100.0, "labourer": 10.0}


class _Labour:
    def __init__(self, employees):
        self.employees = employees
        self.market = types.SimpleNamespace(quote_annual=lambda trade: WAGE_PER_YEAR[trade])
        self.reductions = []

    def staff_snapshot(self):
        return dict(self.employees)

    def add_employed(self, trade, change):
        self.employees[trade] += change

    def employed(self, trade):
        return self.employees[trade]

    def set_employed(self, trade, value):
        self.employees[trade] = value

    def resync_pools(self):
        pass

    def log_staff_reduction(self, reason, before):
        self.reductions.append((reason, before))


def _game(employees):
    labour = _Labour(employees)
    household = types.SimpleNamespace(employees=employees, log=[])
    host = types.SimpleNamespace(workforce=household, view=workforce_stand_in.view_of(household), state=types.SimpleNamespace(household=household, scenario=types.SimpleNamespace(year=120)),
                                 labour=labour)
    host.module = workforce_over(host)
    return host


class ShedUnpayableStaffTest(unittest.TestCase):
    def test_staff_who_cannot_be_paid_leave_and_the_loss_is_logged_with_its_count(self):
        game = _game({"smith": 5.0})
        gone = game.module.shed_unpayable_staff(payroll=500.0, can_pay=200.0)
        self.assertGreater(gone, 0.0)
        self.assertAlmostEqual(game.state.household.employees["smith"], 5.0 - gone)
        (year, line), = game.state.household.log
        self.assertEqual(year, 120)
        self.assertEqual(cause_of(line), "staff_left_unpaid")
        self.assertAlmostEqual(facts_of(line)["staff_gone"], gone)
        self.assertEqual(len(game.labour.reductions), 1)

    def test_a_payroll_the_means_cover_loses_nobody_and_logs_nothing(self):
        game = _game({"smith": 5.0})
        self.assertEqual(game.module.shed_unpayable_staff(payroll=500.0, can_pay=500.0), 0.0)
        self.assertEqual(game.state.household.employees["smith"], 5.0)
        self.assertEqual(game.state.household.log, [])
        self.assertEqual(game.labour.reductions, [])

    def test_a_household_with_no_staff_has_nobody_to_lose(self):
        game = _game({})
        self.assertEqual(game.module.shed_unpayable_staff(payroll=500.0, can_pay=0.0), 0.0)
        self.assertEqual(game.state.household.log, [])


if __name__ == "__main__":
    unittest.main()
