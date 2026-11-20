"""coin_cost: what the coin a run ties up costs, as a share of what the run pays in advance."""

QUICK_TOPIC = True

import math
import types
import unittest

from sim.economy import coin_cost
from sim.economy.producers_close import WORKING_CAPITAL_YEARS_OF_VARIABLE_COST

RATE = 0.08


class ShareCharged(unittest.TestCase):
    def test_the_rate_times_the_years_the_coin_is_tied_up(self):
        self.assertAlmostEqual(coin_cost.share_charged(RATE, 0.5), RATE * 0.5)

    def test_the_years_default_to_the_years_of_running_cost_a_producer_keeps(self):
        self.assertAlmostEqual(coin_cost.share_charged(RATE), RATE * WORKING_CAPITAL_YEARS_OF_VARIABLE_COST)

    def test_no_rate_a_negative_rate_and_a_rate_that_is_no_number_charge_nothing(self):
        for rate in (0.0, -0.03, math.nan, math.inf):
            self.assertEqual(coin_cost.share_charged(rate, 1.0), 0.0)

    def test_no_years_charge_nothing(self):
        self.assertEqual(coin_cost.share_charged(RATE, 0.0), 0.0)
        self.assertEqual(coin_cost.share_charged(RATE, -1.0), 0.0)


class RunCost(unittest.TestCase):
    def test_what_is_paid_in_advance_carries_the_charge_and_what_is_paid_at_the_years_end_does_not(self):
        self.assertAlmostEqual(coin_cost.run_cost(100.0, 30.0, 0.08), 100.0 * 1.08 + 30.0)

    def test_no_charge_leaves_the_plain_sum(self):
        self.assertEqual(coin_cost.run_cost(100.0, 30.0, 0.0), 130.0)


class LeftForHours(unittest.TestCase):
    def test_the_wage_bill_and_its_charge_together_fill_the_room(self):
        wage_bill = coin_cost.left_for_hours(54.0, 0.08)
        self.assertAlmostEqual(wage_bill * 1.08, 54.0)

    def test_no_charge_leaves_the_whole_room(self):
        self.assertEqual(coin_cost.left_for_hours(54.0, 0.0), 54.0)


class ChargeOfARuleSet(unittest.TestCase):
    def setUp(self):
        self.setup = types.SimpleNamespace(currency_id="coin")
        self.view = types.SimpleNamespace(interest_rate=lambda currency: {"coin": RATE}.get(currency))

    def test_no_charge_is_nothing_whatever_the_rate(self):
        self.assertEqual(coin_cost.no_charge(self.setup, self.view), 0.0)

    def test_the_going_rate_is_the_rate_of_the_economys_own_currency(self):
        self.assertAlmostEqual(coin_cost.charge_at_the_going_rate(self.setup, self.view), coin_cost.share_charged(RATE))


if __name__ == "__main__":
    unittest.main()
