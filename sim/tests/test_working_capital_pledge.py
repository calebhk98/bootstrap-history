"""A producer's working-capital request pledges the producer's own assets (cash, goods in hand, plant), not the
loan itself, so the risk markup reflects what stands behind the loan. One plain function, written-out inputs."""
QUICK_TOPIC = True

import unittest

from sim.economy import credit, producers_working_capital

MONEY = "coin"


class WorkingCapitalPledgeTests(unittest.TestCase):
    def test_the_request_pledges_the_producers_assets_not_the_loan(self):
        request = producers_working_capital.request("firm", MONEY, 100.0, 0.08, assets=5000.0)
        self.assertEqual(request.collateral_value, 5000.0)
        self.assertEqual(request.amount, 100.0)
        self.assertEqual(request.maximum_rate, 0.08)
        self.assertEqual(request.years, 1.0)
        self.assertEqual(request.purpose, producers_working_capital.WORKING_CAPITAL_PURPOSE)

    def test_a_producer_with_assets_pays_a_smaller_markup_than_one_whose_only_backing_is_the_loan(self):
        backed = producers_working_capital.request("firm", MONEY, 100.0, 0.08, assets=5000.0)
        bare = producers_working_capital.request("firm", MONEY, 100.0, 0.08, assets=0.0)
        self.assertLess(credit.risk_premium(100.0, backed.collateral_value, 0.0),
                        credit.risk_premium(100.0, bare.collateral_value, 0.0))

    def test_a_producer_holding_nothing_pledges_the_loan_itself(self):
        request = producers_working_capital.request("firm", MONEY, 100.0, 0.08, assets=0.0)
        self.assertEqual(request.collateral_value, 100.0)

    def test_assets_sum_cash_goods_and_plant_and_ignore_a_good_with_no_price(self):
        self.assertEqual(producers_working_capital.pledgeable_assets(10.0, [(2.0, 3.0), (None, 9.0), (1.0, -4.0)], 7.0), 23.0)


if __name__ == "__main__":
    unittest.main()
