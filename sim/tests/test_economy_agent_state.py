"""The agent economy's state budget: it spends what it has, covers a deficit in its policy's order, and what it prints is
booked as money (Complaint 389). Each rule is called on a record written out in the test; that printing reaches prices is
a whole-economy claim, measured with `python3 sim/simulator.py economy-check` (Complaint 473)."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import state_budget, state_finance
from sim.economy.state_policy import StatePolicy
from sim.economy.types import CurrencySpec
from sim.tests.economy_state_fixture import COIN, opened  # noqa: F401  (test_state_printing_scale_rule opens a fixture economy through it)

STATE = "state:fixture"
REVENUE = 1000.0
SUPPLY = 10_000.0


class StubBook:
    """The state's purse and the money supply, with a record of what was booked."""

    def __init__(self, cash=0.0):
        self.cash, self.transfers = cash, []

    def balance(self, agent, currency):
        return self.cash

    def money_supply(self, currency):
        return SUPPLY

    def transfer_many(self, transfers):
        self.transfers.extend(transfers)


def currency(regime):
    return CurrencySpec(COIN, regime, None if regime == "fiat" else "metal", 0.0 if regime == "fiat" else 0.01,
                        STATE, 0.0)


def economy_of(order, regime="fiat", cash=0.0, revenue=REVENUE, **policy_changes):
    """(setup, record, view) of a state with `cash` and last year's `revenue`, financing in `order`."""
    policy = StatePolicy(financing_order=order, **policy_changes)
    setup = types.SimpleNamespace(currency_id=COIN, state_agent=STATE, state_policy=policy, trades={}, unskilled_trade="labourer",
                                  opening_wages={"labourer": 1.0}, working_hours_per_year=2000.0)
    record = types.SimpleNamespace(loans=[], loan_requests=[], currency=currency(regime), book=StubBook(cash), cohorts={},
                                   state_budget=state_budget.StateBudget(revenue=revenue))
    view = types.SimpleNamespace(interest_rate=lambda money: 0.05, chained_price_level=lambda money: 1.0, wage=lambda trade, area: None)
    return setup, record, view


def finance(deficit, order, revenue=REVENUE, regime="fiat"):
    """The deficit financed: (record, (in hand now, expected later, supplied by method))."""
    setup, record, view = economy_of(order, regime)
    return record, state_finance.finance_deficit(setup.state_policy, record, view, setup, deficit, revenue)


class FinancingOrderTests(unittest.TestCase):
    def test_borrowing_comes_first_up_to_its_headroom_and_the_rest_is_printed(self):
        headroom = state_finance.DEBT_LIMIT_YEARS_OF_REVENUE * REVENUE
        record, (_in_hand, expected, supplied) = finance(headroom + 500.0, ("borrow", "issue"))
        self.assertAlmostEqual(supplied["borrow"], headroom)
        self.assertAlmostEqual(supplied["issue"], 500.0)
        self.assertAlmostEqual(expected, headroom)
        self.assertEqual(record.loan_requests[0].borrower, STATE)

    def test_a_deficit_inside_the_headroom_is_only_borrowed(self):
        _record, (_in_hand, _expected, supplied) = finance(100.0, ("borrow", "issue"))
        self.assertEqual(list(supplied), ["borrow"])

    def test_printing_first_leaves_the_credit_market_alone(self):
        record, (in_hand, expected, supplied) = finance(2000.0, ("issue", "borrow"))
        self.assertEqual(list(supplied), ["issue"])
        self.assertAlmostEqual(in_hand, 2000.0)
        self.assertEqual(expected, 0.0)
        self.assertEqual(record.loan_requests, [])

    def test_a_state_with_no_revenue_cannot_borrow_and_falls_back_to_the_next_method(self):
        _record, (_in_hand, _expected, supplied) = finance(300.0, ("borrow", "issue"), revenue=0.0)
        self.assertNotIn("borrow", supplied)
        self.assertAlmostEqual(supplied["issue"], 300.0)

    def test_a_method_the_regime_closes_is_skipped(self):
        _record, (_in_hand, _expected, supplied) = finance(300.0, ("debase", "issue"))
        self.assertEqual(list(supplied), ["issue"])
        _record, (_in_hand, _expected, supplied) = finance(300.0, ("issue", "debase"), regime="struck_coin")
        self.assertEqual(list(supplied), ["debase"])

    def test_nothing_is_financed_without_a_deficit(self):
        _record, financed = finance(0.0, ("borrow", "issue"))
        self.assertEqual(financed, (0.0, 0.0, {}))

    def test_printing_books_the_deficit_to_the_states_purse(self):
        record, _financed = finance(700.0, ("issue",))
        self.assertEqual([(each.payee, each.amount) for each in record.book.transfers], [(STATE, 700.0)])

    def test_debasing_thins_the_metal_behind_each_coin_and_books_the_new_coin(self):
        record, _financed = finance(0.2 * SUPPLY, ("debase",), regime="struck_coin")
        self.assertAlmostEqual(record.currency.backing_per_unit, 0.01 * SUPPLY / (SUPPLY + 0.2 * SUPPLY))
        self.assertAlmostEqual(sum(each.amount for each in record.book.transfers), 0.2 * SUPPLY)


class StateYearTests(unittest.TestCase):
    def plan(self, order, cash, regime="fiat", **policy_changes):
        setup, record, view = economy_of(order, regime, cash, **policy_changes)
        state_budget.plan_year(setup, record, view, [])
        return record.state_budget

    def test_a_stated_programme_beyond_means_runs_a_deficit_it_finances_by_printing(self):
        budget = self.plan(("issue",), cash=100.0, real_spending_target=500.0)
        self.assertAlmostEqual(budget.deficit, 400.0)
        self.assertAlmostEqual(budget.financed["issue"], 400.0)
        self.assertAlmostEqual(budget.issued_total, 400.0)

    def test_a_state_that_spends_what_it_has_runs_no_deficit_and_prints_nothing(self):
        budget = self.plan(("issue",), cash=1500.0)
        self.assertEqual((budget.deficit, budget.issued_total, budget.financed), (0.0, 0.0, {}))

    def test_what_it_plans_to_spend_is_split_between_hours_and_goods_by_its_wage_share(self):
        budget = self.plan(("issue",), cash=1500.0, regime="struck_coin", wage_share=0.25)
        total = budget.wage_budget + budget.goods_budget
        self.assertGreater(total, 0.0)
        self.assertAlmostEqual(budget.wage_budget, 0.25 * total)

    def test_a_state_never_plans_to_spend_more_than_it_holds_and_can_raise(self):
        cash = 100.0
        budget = self.plan(("borrow",), cash=cash, regime="struck_coin", real_spending_target=1e6)
        raised = sum(budget.financed.values())
        self.assertGreater(raised, 0.0)
        self.assertLessEqual(budget.wage_budget + budget.goods_budget, cash + raised + 1e-6)


if __name__ == "__main__":
    unittest.main()
