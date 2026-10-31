"""The opening's households are credited the property income they receive: each cohort's income swaps the property
income it was figured by ownership for the rent it is paid (opening_rent.income_after_rent), and the purse it opens
with holds last close's property income as cash (opening_resting.purse_with_property_income).

Each test calls one plain function with written-out inputs."""
import unittest

from sim.economy import opening_rent, opening_resting

QUICK_TOPIC = True


class IncomeAfterRentTests(unittest.TestCase):
    def test_a_cohort_figured_property_income_it_does_not_receive_keeps_only_its_wages(self):
        income = opening_rent.income_after_rent({"farms": 1000.0}, {"farms": 170.0}, {})
        self.assertAlmostEqual(income["farms"], 830.0)

    def test_a_cohort_paid_more_rent_than_it_was_figured_gains_the_difference(self):
        income = opening_rent.income_after_rent({"town": 2000.0}, {"town": 50.0}, {"town": 271.0})
        self.assertAlmostEqual(income["town"], 2221.0)

    def test_total_income_is_unchanged_when_the_rent_paid_equals_the_property_income_figured(self):
        income = opening_rent.income_after_rent({"farms": 1000.0, "town": 2000.0}, {"farms": 170.0, "town": 50.0},
                                                {"farms": 0.0, "town": 220.0})
        self.assertAlmostEqual(sum(income.values()), 3000.0)

    def test_a_cohort_in_neither_map_keeps_its_income(self):
        income = opening_rent.income_after_rent({"hills": 500.0}, {}, {})
        self.assertEqual(income, {"hills": 500.0})


class PurseWithPropertyIncomeTests(unittest.TestCase):
    def test_the_purse_holds_the_property_income_received_at_the_last_close(self):
        self.assertAlmostEqual(opening_resting.purse_with_property_income(400.0, 271.0), 671.0)

    def test_no_property_income_leaves_the_purse(self):
        self.assertAlmostEqual(opening_resting.purse_with_property_income(400.0, 0.0), 400.0)

    def test_a_negative_property_income_does_not_take_cash_away(self):
        self.assertAlmostEqual(opening_resting.purse_with_property_income(400.0, -10.0), 400.0)


if __name__ == "__main__":
    unittest.main()
