"""Complaint 585: staff paid the going wage leave only at the rate the market moves workers; underpaid staff may go.

The rules are plain functions: the market's own loss share (`on_the_job_loss_share`), the pay a person is on and how it
settles and blends (sim/labour/staff_pay_rules.py), and the year's roll. (Replacement of lost staff:
test_automation_modes.)"""
QUICK_TOPIC = True

import random
import unittest

from sim.engine.seat_defaults import default_policy
from sim.labour.market.clearing import on_the_job_loss_share
from sim.labour.staff_pay_rules import blended_pay, pay_of, roll_trade, settled_pay, wage_bill_of, wage_for_hours_of


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


class PayOfTests(unittest.TestCase):
    def test_pay_kept_at_the_market_follows_the_market_whatever_was_settled(self):
        self.assertEqual(pay_of(300.0, True, 100.0), 300.0)

    def test_pay_not_kept_at_the_market_stays_at_the_settled_figure(self):
        self.assertEqual(pay_of(300.0, False, 100.0), 100.0)

    def test_pay_not_kept_and_never_settled_is_the_going_wage(self):
        self.assertEqual(pay_of(300.0, False, None), 300.0)

    def test_staff_on_the_going_wage_have_no_better_offer_while_the_market_rises(self):
        market = 100.0
        for rising in (market, market * 3.0):
            self.assertEqual(on_the_job_loss_share(pay_of(rising, True, market), rising), 0.0)

    def test_staff_left_at_the_hire_time_figure_may_take_better_offers_when_the_market_rises(self):
        market = 100.0
        pay = pay_of(market * 3.0, False, market)
        self.assertLess(pay, market * 3.0 / 2.0)
        self.assertGreater(on_the_job_loss_share(pay, market * 3.0), 0.0)


class SettledPayTests(unittest.TestCase):
    def test_with_pay_kept_at_the_market_every_trade_held_is_settled_at_the_going_wage(self):
        settled = settled_pay({"smith": 50.0}, ["smith", "mason"], {"smith": 80.0, "mason": 60.0}.get, True)
        self.assertEqual(settled, {"smith": 80.0, "mason": 60.0})

    def test_without_it_the_settled_figure_stays(self):
        self.assertEqual(settled_pay({"smith": 50.0}, ["smith", "mason"], {"smith": 80.0, "mason": 60.0}.get, False),
                         {"smith": 50.0})

    def test_trades_no_longer_held_are_dropped(self):
        self.assertEqual(settled_pay({"smith": 50.0, "cook": 30.0}, ["smith"], {"smith": 80.0}.get, False), {"smith": 50.0})
        self.assertEqual(settled_pay({"smith": 50.0, "cook": 30.0}, ["smith"], {"smith": 80.0}.get, True), {"smith": 80.0})


class BlendedPayTests(unittest.TestCase):
    def test_new_hires_are_averaged_into_the_settled_pay_by_head(self):
        self.assertAlmostEqual(blended_pay(3, 100.0, 1, 200.0), 125.0)

    def test_the_first_hires_set_the_pay(self):
        self.assertAlmostEqual(blended_pay(0, 999.0, 4, 120.0), 120.0)


class WageBillTests(unittest.TestCase):
    def test_the_bill_is_the_head_of_each_trade_times_its_pay(self):
        pay = {"smith": 100.0, "mason": 50.0}
        self.assertAlmostEqual(wage_bill_of({"smith": 2, "mason": 3}, pay.get), 350.0)

    def test_with_pay_kept_at_the_market_the_bill_follows_the_market_up(self):
        bill_before = wage_bill_of({"labourer": 40}, lambda trade: pay_of(100.0, True, 100.0))
        bill_after = wage_bill_of({"labourer": 40}, lambda trade: pay_of(300.0, True, 100.0))
        self.assertAlmostEqual(bill_after, 3.0 * bill_before)


class FounderWageTests(unittest.TestCase):
    """What the founder's own hours earn (Complaint 640): the trade's hourly rate and a capped bonus for reputation."""

    def pay(self, hours=500.0, reputation=0.0):
        return wage_for_hours_of(2000.0, 2000.0, hours, reputation, 0.5, 200.0)

    def test_hours_pay_the_hourly_rate_of_the_yearly_wage(self):
        self.assertAlmostEqual(self.pay(), 500.0)

    def test_reputation_raises_the_rate_in_proportion_to_the_scale(self):
        self.assertAlmostEqual(self.pay(reputation=50.0), 500.0 * 1.25)

    def test_the_bonus_is_capped_however_famous_he_is(self):
        self.assertAlmostEqual(self.pay(reputation=1.0e6), 500.0 * 1.5)

    def test_twice_the_hours_pay_twice_as_much(self):
        self.assertAlmostEqual(self.pay(hours=1000.0, reputation=50.0), 2.0 * self.pay(hours=500.0, reputation=50.0))

    def test_no_hours_earn_nothing(self):
        self.assertEqual(self.pay(hours=0.0, reputation=50.0), 0.0)


class RollTests(unittest.TestCase):
    DEATH_RATE = 0.02

    def test_staff_on_the_going_wage_none_leave_for_better_offers(self):
        died, left, survivors = roll_trade(40, on_the_job_loss_share(100.0, 100.0), self.DEATH_RATE, random.Random(5).random)
        self.assertEqual(left, 0)
        self.assertEqual(survivors, 40 - died)

    def test_underpaid_staff_some_leave(self):
        died, left, survivors = roll_trade(40, on_the_job_loss_share(33.0, 100.0), self.DEATH_RATE, random.Random(5).random)
        self.assertGreater(left, 0)
        self.assertEqual(survivors, 40 - died - left)

    def test_deaths_come_before_offers_in_the_draw(self):
        always_dies = roll_trade(10, 1.0, 1.0, lambda: 0.5)
        self.assertEqual(always_dies, (10, 0, 0))
        always_leaves = roll_trade(10, 1.0, 0.0, lambda: 0.5)
        self.assertEqual(always_leaves, (0, 10, 0))

    def test_a_certain_offer_takes_everyone_who_does_not_die(self):
        died, left, survivors = roll_trade(25, 1.0, self.DEATH_RATE, random.Random(9).random)
        self.assertEqual(survivors, 0)
        self.assertEqual(died + left, 25)

    def test_the_same_draws_give_the_same_roll(self):
        first = roll_trade(40, 0.3, self.DEATH_RATE, random.Random(5).random)
        second = roll_trade(40, 0.3, self.DEATH_RATE, random.Random(5).random)
        self.assertEqual(first, second)

    def test_nobody_on_the_books_rolls_nothing(self):
        self.assertEqual(roll_trade(0, 0.5, self.DEATH_RATE, lambda: self.fail("no draw for nobody")), (0, 0, 0))


if __name__ == "__main__":
    unittest.main()
