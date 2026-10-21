"""More money in circulation raises prices through two rules, each called on inputs built here: a household
holding more cash than usual offers to spend more of it (`goods_orders`), and a market whose buyers have more
to spend on the same supply clears dearer (`goods_market.clear`). The whole-game version, mined metal against the
mean price level of a played civilisation, rode on how a cycling food price happened to fall (Complaint 473) and is
a named scenario for the money stock only (money_regimes_play)."""

QUICK_TOPIC = True

import unittest

from sim.economy import goods_market, households
from sim.economy.types import Bid, Offer
from sim.tests.test_economy_households import BASKET, SPECS, View, budget_total, cohort

INCOME = 100000.0
CASH_ABOVE_USUAL = 400000.0


class CashReachesSpendingTests(unittest.TestCase):
    def spending(self, cash):
        view = View()
        view.interest_rate = lambda currency: 0.05
        return budget_total(households.goods_orders(cohort(), view, cash, INCOME, BASKET, SPECS))

    def test_a_household_holding_more_cash_at_the_same_income_offers_more_for_goods(self):
        self.assertGreater(self.spending(CASH_ABOVE_USUAL), self.spending(2.0 * INCOME))

    def test_more_cash_never_lowers_what_a_household_offers(self):
        offered = [self.spending(cash) for cash in (INCOME, 2.0 * INCOME, 4.0 * INCOME, 8.0 * INCOME)]
        self.assertEqual(offered, sorted(offered))


class BudgetReachesPriceTests(unittest.TestCase):
    def cleared_price(self, budget_each):
        offers = [Offer("farmer", "grain", "area", "t1", 100.0, 1.0)]
        bids = [Bid("buyer:%d" % index, "grain", "area", "t1", 40.0, 40.0, 1.0, 0.5, budget_each)
                for index in range(2)]
        return goods_market.clear(bids, offers, "grain", "area", "coin", None).price

    def test_buyers_with_more_to_spend_on_the_same_supply_clear_at_a_higher_price(self):
        self.assertGreater(self.cleared_price(200.0), self.cleared_price(80.0))


if __name__ == "__main__":
    unittest.main()
