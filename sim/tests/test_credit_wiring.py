"""Complaint 640: the finance module's methods over plain values: spending_power hands the purse, the line and the
ordinary share to the rule; the credit line is set by the standing earning, not by this year's wage-selling; the arrears
banner quotes the standing ledger and wage work only when it beats the standing job. The arithmetic itself is in
test_affordability_and_credit."""
QUICK_TOPIC = True

from types import SimpleNamespace
import unittest

from sim.finance.affordability import spending_power_of
from sim.finance.constants import CREDIT_LINE_EARNING_MULTIPLE, SPENDING_DRAW_SHARE_ORDINARY
from sim.finance.credit_freeze import STALL_MINIMUM_INSOLVENT_YEARS
from sim.finance.state import FinanceSeat
from sim.tests import finance_host


def household(capital=0.0, line=0.0, **views):
    """The module over a purse of `capital`, its credit line fixed at `line`, and years enough in arrears to be stuck."""
    module = finance_host.build(seat=FinanceSeat(insolvent_years=STALL_MINIMUM_INSOLVENT_YEARS), acting_balance=capital,
                                money_per_labour_hour=2.0, **views)
    module.credit_limit = lambda revenue=None, upkeep=None, capital=None: line
    return module


class SpendingPower(unittest.TestCase):
    def test_each_kind_asks_the_rule_with_the_purse_the_line_and_the_ordinary_share(self):
        for kind in ("buy", "start", "open"):
            for capital in (400.0, -50.0, -500.0):
                self.assertEqual(household(capital=capital, line=210.0).spending_power(kind),
                                 spending_power_of(kind, capital, 210.0, SPENDING_DRAW_SHARE_ORDINARY), (kind, capital))

    def test_the_default_kind_is_a_purchase(self):
        module = household(capital=-50.0, line=210.0)
        self.assertEqual(module.spending_power(), module.spending_power("buy"))


class CreditLineSought(unittest.TestCase):
    def test_the_line_follows_the_standing_earning_and_never_asks_for_this_years_revenue(self):
        module = finance_host.build(civilisation={"starting_interest_rate": 0.1}, money_per_labour_hour=2.0, revenue_capacity=1000.0,
                                    agent_rate=0.1, revenue_estimate=lambda: self.fail("this year's revenue was asked for"))
        module.living_cost = lambda revenue=None, upkeep=None, capital=None: 10.0
        base, floor, serviceable = module.credit_line_sought()
        self.assertEqual(base, 1000.0 * CREDIT_LINE_EARNING_MULTIPLE)
        self.assertEqual(floor, 10.0)
        self.assertGreater(serviceable, floor)


class StallDiagnosis(unittest.TestCase):
    def _stalled(self, hours=500.0, best_pays=900.0, standing_pays=0.0, loss_per_year=400.0, interest_rate=0.0, capital=-4000.0, insolvent_years=None):
        labour = SimpleNamespace(
            hours_for_sale=lambda: hours, best_wage_trade=lambda: "smith",
            work_for_wages_dry_run=lambda trade, quoted_hours: (best_pays, None), standing_job_pay=lambda trade: standing_pays)
        module = household(capital=capital, revenue_capacity=0.0, upkeep=0.0, held_trade="labourer", legacy_game=SimpleNamespace(labour=labour))
        module.living_cost = lambda revenue=None, upkeep=None, capital=None: loss_per_year
        module.debt_interest_rate = lambda: interest_rate
        if insolvent_years is not None:
            module.seat.insolvent_years = insolvent_years
        return module

    def test_a_household_in_credit_is_not_stuck(self):
        self.assertIsNone(self._stalled(capital=10.0).stall_diagnosis())

    def test_a_household_not_yet_years_in_arrears_is_not_stuck(self):
        self.assertIsNone(self._stalled(insolvent_years=STALL_MINIMUM_INSOLVENT_YEARS - 1).stall_diagnosis())

    def test_the_banner_quotes_the_standing_loss_and_offers_wage_work_that_beats_the_standing_job(self):
        diagnosis = self._stalled(loss_per_year=400.0, best_pays=900.0, standing_pays=0.0).stall_diagnosis()
        # presentation: the banner quotes the loss and the trade, hours and sum the work would bring
        self.assertIn("400", diagnosis["you_are_stuck"])
        work = [way for way in diagnosis["what_would_change_it"] if way.startswith("work as a smith: 500 ")]
        self.assertEqual(len(work), 1)
        self.assertIn("900", work[0])

    def test_wage_work_that_pays_no_more_than_the_standing_job_is_not_offered(self):
        diagnosis = self._stalled(best_pays=900.0, standing_pays=900.0).stall_diagnosis()
        self.assertFalse([way for way in diagnosis["what_would_change_it"] if way.startswith("work as a ")])

    def test_wage_work_is_offered_only_with_more_than_a_hundred_hours_to_sell(self):
        diagnosis = self._stalled(hours=100.0).stall_diagnosis()
        self.assertFalse([way for way in diagnosis["what_would_change_it"] if way.startswith("work as a ")])

    def test_interest_on_the_arrears_is_named_as_part_of_the_loss(self):
        diagnosis = self._stalled(interest_rate=0.08).stall_diagnosis()
        self.assertTrue([way for way in diagnosis["what_would_change_it"] if "interest on the arrears" in way])  # presentation: names the interest


if __name__ == "__main__":
    unittest.main()
