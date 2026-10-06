"""The agent economy's state budget: it spends what it has, covers a deficit in its policy's order, and what
it prints reaches prices (Complaint 389). Engine-free fixture; each test states a direction, not a figure."""

QUICK_TOPIC = True

import dataclasses
import unittest

from sim.economy import state_finance
from sim.economy.economy import Economy
from sim.economy.state_policy import StatePolicy
from sim.economy.types import CurrencySpec
from sim.tests import economy_fixture as fixture

COIN = "coin"
STATE = "state:fixture"
REVENUE = 1000.0


def fiat_currency():
    return CurrencySpec(COIN, "fiat", None, 0.0, STATE, 0.0)


def opened(order=None, fiat=True, **policy_changes):
    policy = StatePolicy(financing_order=order or StatePolicy().financing_order, **policy_changes)
    changes = {"state_policy": policy}
    if fiat:
        changes["currency"] = fiat_currency()
    return Economy(fixture.small_setup(**changes))


def finance(economy, deficit):
    """The deficit financed from the opening's record: (in hand now, expected later, supplied by method)."""
    return state_finance.finance_deficit(economy.setup.state_policy, economy.record, economy.view(),
                                         economy.setup, deficit, REVENUE)


class FinancingOrderTests(unittest.TestCase):
    def test_borrowing_comes_first_up_to_its_headroom_and_the_rest_is_printed(self):
        economy = opened(("borrow", "issue"))
        headroom = state_finance.DEBT_LIMIT_YEARS_OF_REVENUE * REVENUE
        _in_hand, expected, supplied = finance(economy, headroom + 500.0)
        self.assertAlmostEqual(supplied["borrow"], headroom)
        self.assertAlmostEqual(supplied["issue"], 500.0)
        self.assertAlmostEqual(expected, headroom)
        self.assertEqual(economy.record.loan_requests[0].borrower, STATE)

    def test_a_deficit_inside_the_headroom_is_only_borrowed(self):
        economy = opened(("borrow", "issue"))
        _in_hand, _expected, supplied = finance(economy, 100.0)
        self.assertEqual(list(supplied), ["borrow"])

    def test_printing_first_leaves_the_credit_market_alone(self):
        economy = opened(("issue", "borrow"))
        in_hand, expected, supplied = finance(economy, 2000.0)
        self.assertEqual(list(supplied), ["issue"])
        self.assertAlmostEqual(in_hand, 2000.0)
        self.assertEqual(expected, 0.0)
        self.assertEqual(economy.record.loan_requests, [])

    def test_a_state_with_no_revenue_cannot_borrow_and_falls_back_to_the_next_method(self):
        economy = opened(("borrow", "issue"))
        _in_hand, _expected, supplied = state_finance.finance_deficit(
            economy.setup.state_policy, economy.record, economy.view(), economy.setup, 300.0, 0.0)
        self.assertNotIn("borrow", supplied)
        self.assertAlmostEqual(supplied["issue"], 300.0)

    def test_a_method_the_regime_closes_is_skipped(self):
        fiat = opened(("debase", "issue"))
        _in_hand, _expected, supplied = finance(fiat, 300.0)
        self.assertEqual(list(supplied), ["issue"])
        struck = opened(("issue", "debase"), fiat=False)
        _in_hand, _expected, supplied = finance(struck, 300.0)
        self.assertEqual(list(supplied), ["debase"])

    def test_nothing_is_financed_without_a_deficit(self):
        economy = opened()
        self.assertEqual(finance(economy, 0.0), (0.0, 0.0, {}))

    def test_printing_adds_to_the_supply_and_the_states_purse(self):
        economy = opened(("issue",))
        supply, purse = economy.record.book.money_supply(COIN), economy.record.book.balance(STATE, COIN)
        finance(economy, 700.0)
        self.assertAlmostEqual(economy.record.book.money_supply(COIN) - supply, 700.0)
        self.assertAlmostEqual(economy.record.book.balance(STATE, COIN) - purse, 700.0)

    def test_debasing_thins_the_metal_behind_each_coin(self):
        economy = opened(("debase",), fiat=False)
        before = economy.record.currency.backing_per_unit
        supply = economy.record.book.money_supply(COIN)
        finance(economy, 0.2 * supply)
        self.assertLess(economy.record.currency.backing_per_unit, before)
        self.assertGreater(economy.record.book.money_supply(COIN), supply)


class StateYearTests(unittest.TestCase):
    def test_a_stated_programme_beyond_means_runs_a_deficit_it_finances_by_printing(self):
        setup_economy = opened(("issue",))
        supply = setup_economy.record.book.money_supply(COIN)
        economy = opened(("issue",), real_spending_target=0.5 * supply)
        outcome = economy.step(fixture.quiet_year(economy.setup))
        budget = economy.record.state_budget
        self.assertGreater(budget.deficit, 0.0)
        self.assertGreater(budget.financed.get("issue", 0.0), 0.0)
        self.assertGreater(budget.issued_total, 0.0)
        self.assertTrue(outcome.money_audit.ok)
        self.assertAlmostEqual(outcome.conservation_residual, 0.0, places=6)

    def test_printing_to_spend_raises_prices_above_a_state_that_spends_what_it_has(self):
        supply = opened().record.book.money_supply(COIN)
        control = opened(("issue",))
        printing = opened(("issue",), real_spending_target=0.5 * supply)
        control_levels, printing_levels = [], []
        for _year in range(4):
            control_levels.append(control.step(fixture.quiet_year(control.setup)).basket_price_level)
            printing_levels.append(printing.step(fixture.quiet_year(printing.setup)).basket_price_level)
        self.assertGreater(sum(printing_levels), sum(control_levels))
        self.assertGreater(printing.record.book.money_supply(COIN), control.record.book.money_supply(COIN))

    def test_a_state_that_spends_what_it_has_runs_no_deficit_and_prints_nothing(self):
        economy = opened(("issue",))
        for _year in range(3):
            economy.step(fixture.quiet_year(economy.setup))
            self.assertEqual(economy.record.state_budget.deficit, 0.0)
        self.assertEqual(economy.record.state_budget.issued_total, 0.0)

    def test_what_it_plans_to_spend_is_split_between_hours_and_goods_by_its_wage_share(self):
        economy = opened(("issue",), fiat=False, wage_share=0.25)
        for _year in range(3):
            economy.step(fixture.quiet_year(economy.setup))
        budget = economy.record.state_budget
        total = budget.wage_budget + budget.goods_budget
        self.assertGreater(total, 0.0)
        self.assertLessEqual(budget.wage_budget, 0.25 * total + 1e-6)

    def test_a_state_never_plans_to_spend_more_than_it_holds_and_can_raise(self):
        economy = opened(("borrow",), fiat=False)
        for _year in range(2):
            economy.step(fixture.quiet_year(economy.setup))
        economy.record.state_budget.revenue = REVENUE
        cash = economy.record.book.balance(STATE, COIN)
        economy.step(fixture.quiet_year(economy.setup))
        budget = economy.record.state_budget
        raised = sum(budget.financed.values())
        self.assertGreater(cash, 0.0)
        self.assertLessEqual(budget.wage_budget + budget.goods_budget, cash + raised + 1e-6)


if __name__ == "__main__":
    unittest.main()
