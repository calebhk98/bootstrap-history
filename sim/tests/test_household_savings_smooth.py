"""A household's savings target does not collapse as the inflation it expects reaches the interest rate."""

QUICK_TOPIC = True

import unittest

from sim.economy import households, households_orders
from sim.economy.types import GoodSpec
from sim.tests.test_economy_households import BASKET, SPECS, View, budget_total, cohort


class SavingsTargetTests(unittest.TestCase):
    def target(self, inflation, rate=0.12, surplus=1000.0):
        return households_orders.savings_target(surplus, rate, inflation)

    def test_target_is_not_lost_when_expected_inflation_equals_the_rate(self):
        self.assertGreater(self.target(0.12), 0.0)
        self.assertGreater(self.target(0.20), 0.0)

    def test_target_never_rises_with_expected_inflation(self):
        targets = [self.target(inflation / 100.0) for inflation in range(0, 30)]
        self.assertEqual(targets, sorted(targets, reverse=True))

    def test_target_stays_continuous_across_inflation_equal_to_the_rate(self):
        below, above = self.target(0.11), self.target(0.13)
        self.assertLess(abs(below - above), 0.5 * self.target(0.0))

    def test_no_surplus_income_saves_nothing(self):
        self.assertEqual(self.target(0.12, surplus=0.0), 0.0)


class SpendingTests(unittest.TestCase):
    def spending(self, inflation, rate=0.12):
        view = View()
        view.interest_rate = lambda currency: rate
        orders = households.goods_orders(cohort(expected_inflation=inflation), view, 300000.0, 100000.0,
                                         BASKET, SPECS)
        return budget_total(orders)

    def test_spending_has_no_cliff_where_expected_inflation_reaches_the_rate(self):
        self.assertLess(abs(self.spending(0.13) - self.spending(0.11)), 0.05 * self.spending(0.12))
        self.assertLess(abs(self.spending(0.24) - self.spending(0.12)), 0.1 * self.spending(0.12))

    def test_a_household_keeps_part_of_its_cash_when_inflation_exceeds_the_rate(self):
        self.assertLess(self.spending(0.24), 0.75 * 300000.0)


class SpendingSmoothingTests(unittest.TestCase):
    """Wealth above its target is spent down over the years, not in the one year the target falls."""

    def bids(self, cash=1e6, income=100000.0):
        view = View()
        view.interest_rate = lambda currency: 0.12
        orders = households.goods_orders(cohort(expected_inflation=0.2), view, cash, income, BASKET, SPECS)
        return budget_total(orders)

    def test_spending_from_excess_wealth_adds_at_most_a_limited_share_of_income(self):
        limit = households_orders.WEALTH_DRAWDOWN_LIMIT
        self.assertLessEqual(self.bids(), 100000.0 * (1.0 + limit) * 1.001)

    def test_a_household_short_of_its_target_still_cuts_back(self):
        self.assertLess(self.bids(cash=150000.0), 0.95 * 150000.0)

    def test_spending_scales_with_income_not_with_cash(self):
        self.assertGreater(self.bids(income=400000.0), 2.0 * self.bids(income=100000.0))


class SpendingCutSmoothingTests(unittest.TestCase):
    """A rise in the savings a household wants is met over several years: spending falls by a limited share."""

    def bids(self, **changes):
        view = View()
        view.interest_rate = lambda currency: 0.3
        return budget_total(households.goods_orders(cohort(**changes), view, 150000.0, 100000.0, BASKET, SPECS))

    def test_spending_falls_by_at_most_the_limit_from_expected_spending(self):
        expected = 120000.0
        floor = (1.0 - households_orders.SPENDING_CUT_LIMIT) * expected
        self.assertGreaterEqual(self.bids(expected_spending=expected, expected_floor_cost=1.0), floor * 0.95)

    def test_a_household_with_no_history_is_not_held_up(self):
        self.assertLess(self.bids(), self.bids(expected_spending=120000.0, expected_floor_cost=1.0))

    def test_a_first_year_with_little_income_so_far_spends_its_wealth_at_the_pace_of_its_usual_income(self):
        def spending(**changes):
            view = View()
            view.interest_rate = lambda currency: 0.12
            return budget_total(households.goods_orders(cohort(expected_inflation=0.2, **changes), view, 1e6,
                                                        20000.0, BASKET, SPECS))
        self.assertGreater(spending(last_year_income=100000.0), 1.5 * spending())


class SpendingRiseSmoothingTests(unittest.TestCase):
    """A rise in spending is bounded by expected spending in a running economy, and not in a settling one."""

    def bids(self, expected=60000.0, **orders_arguments):
        view = View()
        view.interest_rate = lambda currency: 0.12
        household = cohort(expected_inflation=0.2, expected_spending=expected, expected_floor_cost=1.0)
        return budget_total(households.goods_orders(household, view, 1e6, 40000.0, BASKET, SPECS, **orders_arguments))

    def test_spending_rises_by_at_most_the_limit_over_expected_spending(self):
        ceiling = (1.0 + households_orders.SPENDING_CUT_LIMIT) * 60000.0
        self.assertLessEqual(self.bids(), ceiling * 1.001)

    def test_a_settling_economy_lets_spending_rise_as_far_as_wealth_allows(self):
        self.assertGreater(self.bids(expected=25000.0, smooth_rise=False), 1.5 * self.bids(expected=25000.0))


class UnsoldGoodTests(unittest.TestCase):
    """A good with no seller has no price, so it draws no bid and its need's money goes to goods that have one."""
    SHELTER = households.make_basket({
        "needs": {"shelter": {"surplus_budget_share": 1.0, "subsistence_per_capita_per_year": 0.0}},
        "goods": {"brick": {"satisfies": {"shelter": 1.0}}, "lime": {"satisfies": {"shelter": 0.5}}}}, {})
    SPECS = {"brick": GoodSpec("brick", 1.0, 0.0, 5.0, "brick"), "lime": GoodSpec("lime", 1.0, 0.0, 5.0, "lime")}

    def bids(self, prices):
        view = View(prices)
        view.prices = dict(prices)
        orders = households.goods_orders(cohort(), view, 1e6, 1e6, self.SHELTER, self.SPECS)
        return {bid.good: bid.budget for bid in orders.bids}

    def test_the_cheapest_good_without_a_price_takes_none_of_the_need(self):
        priced = self.bids({"brick": 4.0, "lime": 1.0})
        unpriced = self.bids({"brick": 4.0})
        self.assertIn("lime", priced)
        self.assertNotIn("lime", unpriced)
        self.assertGreater(unpriced["brick"], priced.get("brick", 0.0))


if __name__ == "__main__":
    unittest.main()
