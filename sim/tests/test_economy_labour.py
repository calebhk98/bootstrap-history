"""What a worker asks (the outside option and danger pay) and what a training costs."""
import unittest

import types

from sim.economy import labour, year_labour
from sim.economy.households_orders import HOUSEHOLD_TIME_PREFERENCE


class TrainingPremiumTests(unittest.TestCase):
    def test_the_premium_discounts_training_at_the_familys_own_time_preference(self):
        # the family gives up consumption to train a child; a spike in the loan market's rate must not
        # turn into a spike in skilled wages
        setup = types.SimpleNamespace(trades={"smith": types.SimpleNamespace(training_years=5.0)})
        self.assertAlmostEqual(year_labour.trade_premium(setup, "smith"),
                               labour.training_premium(5.0, HOUSEHOLD_TIME_PREFERENCE, year_labour.CAREER_YEARS))


class ReservationAndTrainingTests(unittest.TestCase):
    def test_reservation_wage_is_the_outside_option_without_danger(self):
        self.assertAlmostEqual(labour.reservation_wage(2000.0, 2000.0, 0.0, 30.0), 1.0)

    def test_danger_raises_the_reservation_wage(self):
        safe = labour.reservation_wage(2000.0, 2000.0, 0.001, 30.0)
        risky = labour.reservation_wage(2000.0, 2000.0, 0.02, 30.0)
        self.assertGreater(safe, 1.0)
        self.assertGreater(risky, safe)

    def test_training_premium_repays_the_forgone_income_as_an_annuity(self):
        premium = labour.training_premium(3.0, 0.05, 30.0)
        forgone_at_start = sum(1.05 ** (3 - year) for year in range(1, 4))
        annuity_factor = sum(1.05 ** -year for year in range(1, 31))
        self.assertAlmostEqual(premium, forgone_at_start / annuity_factor, places=9)

    def test_training_premium_without_interest_spreads_the_years(self):
        self.assertAlmostEqual(labour.training_premium(2.0, 0.0, 20.0), 0.1)
        self.assertEqual(labour.training_premium(0.0, 0.05, 20.0), 0.0)

    def test_longer_training_costs_more(self):
        self.assertGreater(labour.training_premium(5.0, 0.05, 30.0), labour.training_premium(2.0, 0.05, 30.0))


if __name__ == "__main__":
    unittest.main()
