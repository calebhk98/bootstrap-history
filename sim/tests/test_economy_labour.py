"""What a worker asks (the outside option and danger pay) and the trade premium quotes use."""

QUICK_TOPIC = True

import unittest

import types

from sim.economy import labour, year_labour
from sim.labour.api import wages
from sim.economy.households_orders import HOUSEHOLD_TIME_PREFERENCE


class TrainingPremiumTests(unittest.TestCase):
    def test_the_premium_discounts_training_at_the_familys_own_time_preference(self):
        # the family gives up consumption to train a child; a spike in the loan market's rate must not
        # turn into a spike in skilled wages
        setup = types.SimpleNamespace(trades={"smith": types.SimpleNamespace(training_years=5.0)})
        self.assertAlmostEqual(year_labour.trade_premium(setup, "smith"),
                               wages.training_premium(5.0, HOUSEHOLD_TIME_PREFERENCE, year_labour.CAREER_YEARS) - 1.0)


class ReservationAndTrainingTests(unittest.TestCase):
    def test_reservation_wage_is_the_outside_option_without_danger(self):
        self.assertAlmostEqual(labour.reservation_wage(2000.0, 2000.0, 0.0, 30.0), 1.0)

    def test_danger_raises_the_reservation_wage(self):
        safe = labour.reservation_wage(2000.0, 2000.0, 0.001, 30.0)
        risky = labour.reservation_wage(2000.0, 2000.0, 0.02, 30.0)
        self.assertGreater(safe, 1.0)
        self.assertGreater(risky, safe)


if __name__ == "__main__":
    unittest.main()
