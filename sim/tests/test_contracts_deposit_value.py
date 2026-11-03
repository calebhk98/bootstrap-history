"""A deposit topped up keeps the lender's own-unit value of what was already in the pool (`Contracts.deposit`)."""
QUICK_TOPIC = True

import unittest

from sim.contracts import Contracts


class TopUp(unittest.TestCase):
    def test_a_top_up_at_another_unit_value_averages_over_the_whole_deposit(self):
        contracts = Contracts()
        contracts.deposit("cohort:a", "pool", "coin", 10.0, unit_value=0.5)
        contracts.deposit("cohort:a", "pool", "coin", 10.0, unit_value=1.0)
        self.assertAlmostEqual(contracts.deposit_value("cohort:a"), 15.0)

    def test_a_first_deposit_is_worth_its_unit_value(self):
        contracts = Contracts()
        contracts.deposit("cohort:a", "pool", "coin", 10.0, unit_value=0.5)
        self.assertAlmostEqual(contracts.deposit_value("cohort:a"), 5.0)


if __name__ == "__main__":
    unittest.main()
