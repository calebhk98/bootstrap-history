"""Complaint 473: what a producer's year close pays its owner today. close_year proposes every unit of cash above
the working-capital target as a dividend, whatever the year's earnings were."""

QUICK_TOPIC = True

import unittest

from sim.economy import producers_close
from sim.tests.test_economy_producers import FARM, farm_view, farmer


class TodaysDividendTests(unittest.TestCase):
    def test_a_loss_year_still_pays_out_all_cash_above_the_target(self):
        view = farm_view(2.0, cash=500.0)
        result = producers_close.close_year(farmer(capacity_runs=10.0), FARM, 10.0, 50.0, view, 4.0)
        paid = sum(transfer.amount for transfer in result.transfers)
        self.assertAlmostEqual(paid, 500.0 - result.producer.cash_target)
        self.assertGreater(paid, 0.0)


if __name__ == "__main__":
    unittest.main()
