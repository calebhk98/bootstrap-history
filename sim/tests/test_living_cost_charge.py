"""Complaint 524: a year in arrears with no income charges living costs without the dependants its income cannot carry, and
nets off the wages paid in advance. `living_cost_charged` on numbers built here. Which dependants the income cannot carry is
test_ruined_household_dependants."""
import unittest

from sim.engine.living_cost_charge import living_cost_charged

QUICK_TOPIC = True


class LivingCostCharged(unittest.TestCase):

    def test_the_whole_cost_is_charged_when_nothing_is_shed_or_prepaid(self):
        self.assertEqual(living_cost_charged(400.0, 0.0, 0.0), 400.0)

    def test_the_dependants_the_income_cannot_carry_are_not_charged(self):
        self.assertEqual(living_cost_charged(400.0, 100.0, 0.0), 300.0)

    def test_wages_paid_in_advance_come_off(self):
        self.assertEqual(living_cost_charged(400.0, 0.0, 150.0), 250.0)

    def test_both_come_off_together(self):
        self.assertEqual(living_cost_charged(400.0, 100.0, 150.0), 150.0)

    def test_an_advance_larger_than_the_cost_leaves_nothing_to_charge_and_not_less(self):
        self.assertEqual(living_cost_charged(400.0, 100.0, 1000.0), 0.0)

    def test_shedding_every_dependant_of_a_cost_that_is_all_dependants_charges_nothing(self):
        self.assertEqual(living_cost_charged(100.0, 100.0, 0.0), 0.0)


if __name__ == "__main__":
    unittest.main()
