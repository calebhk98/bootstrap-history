"""The debt a seat's earning can service is the one carried-debt function every borrower uses (`capital_market.serviceable_debt`)
at the debt-service share every borrower uses; dearer money than the opening's carries less, cheaper money no more."""

QUICK_TOPIC = True

import unittest

from sim.economy.api import opening_market_rate
from sim.finance.constants import DEBT_SERVICE_SHARE_OF_SURPLUS
from sim.world import capital_market

from . import finance_host


def serviceable_at(market_rate, earning=1000.0, floor=10.0):
    module = finance_host.build(civilisation={"starting_interest_rate": 0.1}, revenue_capacity=earning, agent_rate=market_rate)
    module.living_cost = lambda revenue=None, upkeep=None, capital=None: floor
    return module.credit_line_sought()[2]


class SeatServiceable(unittest.TestCase):
    def test_dearer_money_than_the_opening_carries_the_shared_function_at_the_years_share(self):
        opening = opening_market_rate()
        market = opening * 2.0
        expected = 10.0 + capital_market.serviceable_debt(1000.0 - 10.0 * market, market, DEBT_SERVICE_SHARE_OF_SURPLUS)
        self.assertAlmostEqual(serviceable_at(market), expected)

    def test_cheaper_money_than_the_opening_carries_no_more_than_the_opening_does(self):
        opening = opening_market_rate()
        market = opening / 2.0
        carried = (serviceable_at(market) - 10.0) / (1000.0 - 10.0 * market)
        self.assertAlmostEqual(carried, DEBT_SERVICE_SHARE_OF_SURPLUS / opening)


if __name__ == "__main__":
    unittest.main()
