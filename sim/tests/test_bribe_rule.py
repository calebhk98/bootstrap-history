"""Complaint 640: a bribe buys down scandal and feeds the year's bribes into protection, takes no more than both can use, and
refuses a sum that is too small to move anything or more than the purse holds, changing nothing. The rule is
`bribe_rules` (plain figures in, a plan or a refusal out); the command is checked on the projects module for what it sends."""
QUICK_TOPIC = True

import unittest

from sim.agents.api import edges
from sim.ledger.api import PayEdge
from sim.projects.api import Bribe, ChangeStanding, bribe_rules, constants
from sim.tests import module_harness, projects_host

HOUR_MONEY = 2.0
INCOME = 1000.0
PER_POINT = constants.BRIBE_LABOUR_HOURS_PER_SCANDAL_POINT * HOUR_MONEY


def plan(amount, scandal=2.0, bribes_ytd=0.0, weight=1.0):
    return bribe_rules.plan(amount, scandal, bribes_ytd, INCOME, weight, constants.BRIBE_MEMORY_DECAY,
                            constants.BRIBE_PROTECTION_CAP, constants.BRIBE_INCOME_SHARE, PER_POINT)


def refusal(amount, scandal=2.0, capital=1.0e9, bribes_ytd=0.0, weight=1.0):
    return bribe_rules.refusal_for(amount, capital, scandal, bribes_ytd, INCOME, weight, constants.BRIBE_MEMORY_DECAY,
                                   constants.BRIBE_PROTECTION_CAP, constants.BRIBE_INCOME_SHARE)


class PlanTests(unittest.TestCase):
    def test_a_bribe_lowers_scandal_by_the_sum_over_the_price_of_a_point(self):
        self.assertAlmostEqual(plan(PER_POINT).scandal, 1.0)

    def test_the_year_to_date_keeps_the_decayed_old_sum_and_the_new_one(self):
        self.assertAlmostEqual(plan(PER_POINT, bribes_ytd=100.0).bribes_year_to_date, constants.BRIBE_MEMORY_DECAY * 100.0 + PER_POINT)

    def test_a_sum_beyond_what_scandal_and_protection_can_use_is_not_all_taken(self):
        useful_ceiling = max(0.5 * PER_POINT, constants.BRIBE_PROTECTION_CAP * INCOME * constants.BRIBE_INCOME_SHARE)
        taken = plan(100.0 * useful_ceiling, scandal=0.5)
        self.assertAlmostEqual(taken.paid, useful_ceiling)
        self.assertAlmostEqual(taken.refused, 99.0 * useful_ceiling)
        self.assertEqual(taken.scandal, 0.0)


class RefusalTests(unittest.TestCase):
    def test_a_zero_sum_is_refused(self):
        self.assertEqual(refusal(0.0).cause, "not_positive")

    def test_more_than_the_purse_holds_is_refused(self):
        self.assertEqual(refusal(60.0, capital=50.0).cause, "over_capital")

    def test_with_no_scandal_too_little_to_move_protection_is_refused_with_the_sum_that_would_begin_to(self):
        found = refusal(1.0, scandal=0.0)
        self.assertEqual(found.cause, "too_little")
        self.assertGreater(found.floor, 1.0)

    def test_with_no_scandal_and_protection_at_its_cap_the_refusal_says_so(self):
        cap_income = INCOME * constants.BRIBE_INCOME_SHARE
        found = refusal(1.0, scandal=0.0, bribes_ytd=10.0 * cap_income)
        self.assertEqual(found.cause, "already_protected")

    def test_with_no_scandal_a_serious_sum_still_buys_protection(self):
        self.assertIsNone(refusal(100.0, scandal=0.0))
        self.assertEqual(plan(100.0, scandal=0.0).paid, 100.0)


def briber(scandal=2.0, capital=1.0e9, bribes_ytd=0.0):
    return projects_host.build(
        acting_balance=capital, revenue_estimate=INCOME, money_per_labour_hour=HOUR_MONEY,
        standing={"protection": 0.0, "scandal": scandal, "bribes_year_to_date": bribes_ytd})


class BribeCommand(unittest.TestCase):
    def test_the_sum_is_paid_to_officials_and_the_standing_is_set_for_polity_to_recalculate_protection_from(self):
        module = briber(scandal=2.0, bribes_ytd=100.0)
        ok, _note = module.bribe(Bribe(PER_POINT))
        self.assertTrue(ok)
        self.assertEqual(module_harness.sent(module), [
            PayEdge(edges.EDGE_OFFICIALS, PER_POINT, "bribes"),
            ChangeStanding(scandal=plan(PER_POINT, bribes_ytd=100.0).scandal,
                           bribes_year_to_date=constants.BRIBE_MEMORY_DECAY * 100.0 + PER_POINT)])

    def test_a_refused_bribe_sends_nothing(self):
        for amount, capital in ((0.0, 1.0e9), (60.0, 50.0)):
            module = briber(capital=capital)
            ok, _note = module.bribe(Bribe(amount))
            self.assertFalse(ok)
            self.assertEqual(module_harness.sent(module), [])


if __name__ == "__main__":
    unittest.main()
