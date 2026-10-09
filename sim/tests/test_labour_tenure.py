"""Complaint 111: tenure is worker-years a trade has spent running a technique, held in the labour core."""

QUICK_TOPIC = True

import unittest

from sim.labour import api as labour


class Tenure(unittest.TestCase):

    def test_years_add_by_trade_and_sum_over_trades(self):
        tenure = {}
        labour.add_tenure(tenure, "loom", {"weaver": 3.0, "carpenter": 1.0})
        labour.add_tenure(tenure, "loom", {"weaver": 2.0})
        self.assertEqual(labour.tenure_by_trade(tenure, "loom"), {"weaver": 5.0, "carpenter": 1.0})
        self.assertEqual(labour.tenure_held(tenure, "loom"), 6.0)
        self.assertEqual(labour.tenure_held(tenure, "anvil"), 0.0)

    def test_tenure_fades_at_the_rate_people_leave_work(self):
        tenure = {"weaver": {"loom": 10.0}}
        labour.fade_tenure(tenure, 0.1)
        self.assertAlmostEqual(tenure["weaver"]["loom"], 9.0)

    def test_a_worker_who_changes_trade_carries_nothing(self):
        tenure = {"weaver": {"loom": 10.0}, "smith": {"loom": 4.0}}
        share = labour.outflow_shares({"weaver": 100.0, "smith": 50.0}, {"weaver": 45.0, "smith": 60.0}, 0.1)
        self.assertAlmostEqual(share["weaver"], 0.5)
        self.assertEqual(share["smith"], 0.0)
        labour.fade_tenure(tenure, 0.0, share)
        self.assertAlmostEqual(tenure["weaver"]["loom"], 5.0)
        self.assertAlmostEqual(tenure["smith"]["loom"], 4.0)

    def test_growth_in_a_trade_is_not_an_outflow(self):
        self.assertEqual(labour.outflow_shares({"weaver": 100.0}, {"weaver": 200.0}, 0.1), {"weaver": 0.0})
        self.assertEqual(labour.outflow_shares({}, {"weaver": 200.0}, 0.1), {"weaver": 0.0})


if __name__ == "__main__":
    unittest.main()
