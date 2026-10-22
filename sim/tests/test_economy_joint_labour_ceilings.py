"""The maximum wages of one run's trades share the run's surplus, so all its hours at those wages cost no more
than the run earns (Complaints/678)."""

QUICK_TOPIC = True

import unittest

from sim.economy.labour_ceilings import joint_labour_ceilings


def bill(hours, wages):
    return sum(hours[trade] * wages[trade] for trade in hours)


class JointLabourCeilings(unittest.TestCase):
    def test_a_one_trade_run_gets_the_whole_surplus(self):
        ceilings = joint_labour_ceilings({"smith": 4.0}, {"smith": 1.5}, surplus=20.0)
        self.assertAlmostEqual(ceilings["smith"], 5.0)

    def test_two_trades_never_bid_more_than_the_surplus_in_all(self):
        hours = {"plumber": 2.0, "mason": 6.0}
        wages = {"plumber": 0.5, "mason": 0.3}
        last_bill = bill(hours, wages)
        for surplus in (0.5 * last_bill, last_bill, 3.0 * last_bill, 100.0 * last_bill):
            ceilings = joint_labour_ceilings(hours, wages, surplus)
            self.assertLessEqual(bill(hours, ceilings), surplus * (1.0 + 1e-9))

    def test_a_paying_run_lets_every_trade_keep_at_least_its_last_wage(self):
        hours = {"plumber": 2.0, "mason": 6.0}
        wages = {"plumber": 0.5, "mason": 0.3}
        ceilings = joint_labour_ceilings(hours, wages, surplus=bill(hours, wages) * 1.7)
        for trade in hours:
            self.assertGreaterEqual(ceilings[trade], wages[trade])

    def test_a_trade_with_no_wage_seen_shares_by_hours(self):
        ceilings = joint_labour_ceilings({"a": 1.0, "b": 3.0}, {"a": 0.0, "b": 0.0}, surplus=8.0)
        self.assertAlmostEqual(ceilings["a"], 2.0)
        self.assertAlmostEqual(ceilings["b"], 2.0)

    def test_no_surplus_bids_nothing(self):
        ceilings = joint_labour_ceilings({"a": 1.0}, {"a": 1.0}, surplus=-3.0)
        self.assertEqual(ceilings["a"], 0.0)


if __name__ == "__main__":
    unittest.main()
