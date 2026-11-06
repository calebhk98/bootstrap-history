"""Complaint 585: staff paid the going wage leave only at the rate the market moves workers; underpaid staff may go.

The rules are plain functions: the market's own loss share (`on_the_job_loss_share`) and the pay rules in
sim/labour/staff_pay_rules.py. (Replacement of lost staff: test_automation_modes.)"""
QUICK_TOPIC = True

import unittest

from sim.engine.seat_defaults import default_policy
from sim.labour.market.clearing import on_the_job_loss_share
from sim.labour.staff_pay_rules import wage_bill_of, wage_for_hours_of


class MarketLossShareTests(unittest.TestCase):
    def test_nothing_leaves_an_employer_paying_the_going_wage(self):
        self.assertEqual(on_the_job_loss_share(100.0, 100.0), 0.0)

    def test_nothing_leaves_an_employer_paying_more(self):
        self.assertEqual(on_the_job_loss_share(120.0, 100.0), 0.0)

    def test_some_leave_an_employer_paying_less(self):
        self.assertTrue(0.0 < on_the_job_loss_share(80.0, 100.0) <= 1.0)

    def test_the_further_below_the_market_the_more_leave(self):
        self.assertGreater(on_the_job_loss_share(50.0, 100.0), on_the_job_loss_share(90.0, 100.0))


class DefaultPolicyTests(unittest.TestCase):
    def test_pay_kept_at_the_market_is_the_default_policy_for_a_player_and_for_the_optimizer(self):
        self.assertIs(default_policy(manual=True)["keep_pay_at_market"], True)
        self.assertIs(default_policy(manual=False)["keep_pay_at_market"], True)


class WageBillTests(unittest.TestCase):
    def test_the_bill_is_the_head_of_each_trade_times_its_pay(self):
        pay = {"smith": 100.0, "mason": 50.0}
        self.assertAlmostEqual(wage_bill_of({"smith": 2, "mason": 3}, pay.get), 350.0)


class FounderWageTests(unittest.TestCase):
    """What the founder's own hours earn (Complaint 640): the trade's one hourly rate."""

    def pay(self, hours=500.0):
        return wage_for_hours_of(2000.0, 2000.0, hours)

    def test_hours_pay_the_hourly_rate_of_the_yearly_wage(self):
        self.assertAlmostEqual(self.pay(), 500.0)

    def test_twice_the_hours_pay_twice_as_much(self):
        self.assertAlmostEqual(self.pay(hours=1000.0), 2.0 * self.pay(hours=500.0))

    def test_no_hours_earn_nothing(self):
        self.assertEqual(self.pay(hours=0.0), 0.0)


if __name__ == "__main__":
    unittest.main()
