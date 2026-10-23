"""Complaint 640: the credit mixin's methods over a stand-in household: spending_power hands the purse, the line and the
ordinary share to the rule; the credit line is set by the standing earning, not by this year's wage-selling; the arrears
banner quotes the standing ledger and wage work only when it beats the standing job. The arithmetic itself is in
test_affordability_and_credit."""
QUICK_TOPIC = True

import types
import unittest

from sim.engine.affordability import spending_power_of
from sim.engine.credit_freeze import STALL_MINIMUM_INSOLVENT_YEARS
from sim.engine.economy_credit import CreditMixin


class Household(CreditMixin):
    """What spending_power, credit_line_sought and stall_diagnosis read."""

    def __init__(self, capital=0.0, line=0.0):
        self.line = line
        self.price_index = 1.0
        self.civ = {"starting_interest_rate": 0.1}
        self.state = types.SimpleNamespace(
            household=types.SimpleNamespace(capital=capital, reputation=0.0, insolvent_years=STALL_MINIMUM_INSOLVENT_YEARS),
            holdings=types.SimpleNamespace(forest_ha=0.0), projects=types.SimpleNamespace(operating=set()),
            acting_seat="founder")
        self.nodes = {}
        self.labour = types.SimpleNamespace(money_per_labour_hour=lambda: 2.0)

    def credit_limit(self, _rev=None, _upkeep=None, _capital=None):
        return self.line


class SpendingPower(unittest.TestCase):
    def test_each_kind_asks_the_rule_with_the_purse_the_line_and_the_ordinary_share(self):
        for kind in ("buy", "start", "open"):
            for capital in (400.0, -50.0, -500.0):
                household = Household(capital=capital, line=210.0)
                self.assertEqual(household.spending_power(kind),
                                 spending_power_of(kind, capital, 210.0, household.SPENDING_DRAW_SHARE_ORDINARY),
                                 (kind, capital))

    def test_the_default_kind_is_a_purchase(self):
        household = Household(capital=-50.0, line=210.0)
        self.assertEqual(household.spending_power(), household.spending_power("buy"))


class CreditLineSought(unittest.TestCase):
    def test_the_line_follows_the_standing_earning_and_never_asks_for_this_years_revenue(self):
        household = Household()
        household.revenue_capacity = lambda: 1000.0
        household.effect_sum = lambda channel, base: base
        household.upkeep = lambda: 0.0
        household.living_cost = lambda _rev=None, _upkeep=None, _capital=None: 10.0
        household.market_rate = lambda: 0.1
        household.credit_limit = types.MethodType(CreditMixin.credit_limit, household)
        household.market_credit_room = lambda actor_id: None
        base, floor, serviceable = household.credit_line_sought()
        self.assertEqual(base, 1000.0 * household.CREDIT_LINE_EARNING_MULTIPLE)
        self.assertEqual(floor, 10.0)
        self.assertGreater(serviceable, floor)
        self.assertFalse(hasattr(household, "revenue"))


class StallDiagnosis(unittest.TestCase):
    def _stalled(self, hours=500.0, best_pays=900.0, standing_pays=0.0, loss_per_year=400.0):
        household = Household(capital=-4000.0)
        household.revenue_capacity = lambda: 0.0
        household.upkeep = lambda: 0.0
        household.living_cost = lambda _rev=None, _upkeep=None: loss_per_year
        household.mine_operating_cost = lambda: 0.0
        household.debt_interest_rate = lambda: 0.0
        household.held_trade = lambda: "labourer"
        household.labour = types.SimpleNamespace(
            hours_for_sale=lambda: hours, best_wage_trade=lambda: "smith",
            work_for_wages_dry_run=lambda trade, quoted_hours: (best_pays, None),
            standing_job_pay=lambda trade: standing_pays, wage_bill=lambda: 0.0)
        return household

    def test_a_household_in_credit_is_not_stuck(self):
        household = self._stalled()
        household.state.household.capital = 10.0
        self.assertIsNone(household.stall_diagnosis())

    def test_a_household_not_yet_years_in_arrears_is_not_stuck(self):
        household = self._stalled()
        household.state.household.insolvent_years = STALL_MINIMUM_INSOLVENT_YEARS - 1
        self.assertIsNone(household.stall_diagnosis())

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
        household = self._stalled()
        household.debt_interest_rate = lambda: 0.08
        diagnosis = household.stall_diagnosis()
        self.assertTrue([way for way in diagnosis["what_would_change_it"] if "interest on the arrears" in way])  # presentation: names the interest


if __name__ == "__main__":
    unittest.main()
