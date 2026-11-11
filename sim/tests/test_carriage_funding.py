"""A merchant's carrier bids are bounded by its purse, and its working-capital loan covers the wage bill of the hours its plan wants
(Complaint 613). Each test calls one function on written-out figures."""
import unittest

from sim.economy import carriage_funding


class WageBillTests(unittest.TestCase):
    def test_the_bill_is_hours_times_wage_summed(self):
        self.assertEqual(carriage_funding.wage_bill([(10.0, 0.5), (4.0, 2.0)]), 13.0)


class FundedShareTests(unittest.TestCase):
    def test_cash_that_covers_the_bill_funds_all_of_it(self):
        self.assertEqual(carriage_funding.funded_share(10.0, 10.0), 1.0)

    def test_cash_that_covers_a_quarter_funds_a_quarter(self):
        self.assertEqual(carriage_funding.funded_share(8.0, 2.0), 0.25)

    def test_no_cash_funds_nothing(self):
        self.assertEqual(carriage_funding.funded_share(8.0, 0.0), 0.0)
        self.assertEqual(carriage_funding.funded_share(8.0, -3.0), 0.0)

    def test_no_bill_needs_no_cash(self):
        self.assertEqual(carriage_funding.funded_share(0.0, 0.0), 1.0)


class FundBidsTests(unittest.TestCase):
    def test_a_merchant_with_cash_for_a_tenth_of_its_bill_bids_a_tenth_of_its_hours(self):
        figures = [("m1", "porter", "work@a", 1000.0, 3.0)]
        found = carriage_funding.fund_bids(figures, lambda trade, area: 2.0, {"m1": 200.0}.get)
        self.assertEqual(found, [("m1", "porter", "work@a", 100.0, 3.0)])

    def test_the_share_is_one_for_all_of_a_merchants_bids_and_not_another_merchants(self):
        figures = [("m1", "porter", "work@a", 100.0, 3.0), ("m1", "porter", "work@b", 100.0, 3.0), ("m2", "porter", "work@a", 100.0, 3.0)]
        wage = {"work@a": 1.0, "work@b": 3.0}
        found = carriage_funding.fund_bids(figures, lambda trade, area: wage[area], {"m1": 200.0, "m2": 1000.0}.get)
        self.assertEqual([(each[0], each[2], each[3]) for each in found],
                         [("m1", "work@a", 50.0), ("m1", "work@b", 50.0), ("m2", "work@a", 100.0)])

    def test_a_merchant_with_no_cash_posts_no_bid(self):
        self.assertEqual(carriage_funding.fund_bids([("m1", "porter", "work@a", 5.0, 3.0)], lambda trade, area: 1.0, {"m1": 0.0}.get), [])


class LoanWantedTests(unittest.TestCase):
    def test_the_loan_is_the_wage_bill_the_cash_does_not_cover(self):
        self.assertEqual(carriage_funding.loan_wanted(50.0, 80.0, 20.0), 30.0)

    def test_cash_enough_asks_for_nothing(self):
        self.assertIsNone(carriage_funding.loan_wanted(50.0, 80.0, 60.0))

    def test_hours_worth_less_than_their_wages_are_not_borrowed_for(self):
        self.assertIsNone(carriage_funding.loan_wanted(50.0, 40.0, 0.0))

    def test_no_bill_asks_for_nothing(self):
        self.assertIsNone(carriage_funding.loan_wanted(0.0, 40.0, 0.0))


if __name__ == "__main__":
    unittest.main()
