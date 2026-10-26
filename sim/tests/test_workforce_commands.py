"""The commands the workforce module applies, on a module built over plain household figures, and the rules they call."""
QUICK_TOPIC = True

import random
import unittest
from types import SimpleNamespace

from sim.tests import module_harness
from sim.workforce import rules as workforce_rules
from sim.workforce.api import NoteTradeSpread, PressLabour, ReportStaffReduction, ScaleDeputies, SetEmployed, TakeWageFallback
from sim.workforce.api import CloseHoursYear
from sim.workforce.constants import WAGE_FALLBACK_LIVING_COST_YEARS, WAGE_FALLBACK_MAX_HOURS, WAGE_FALLBACK_MIN_HOURS
from sim.workforce.module import Workforce


class SurvivingPeople(unittest.TestCase):
    def test_everyone_survives_a_share_of_one_and_no_one_a_share_of_zero(self):
        self.assertEqual(workforce_rules.surviving_people(random.Random(1), 40.0, 1.0), 40.0)
        self.assertEqual(workforce_rules.surviving_people(random.Random(1), 40.0, 0.0), 0.0)

    def test_the_headcount_is_whole_and_one_draw_is_made_per_person(self):
        dice = random.Random(3)
        kept = workforce_rules.surviving_people(dice, 12.4, 0.5)
        self.assertEqual(kept, float(int(kept)))
        mirror = random.Random(3)
        for _ in range(12):
            mirror.random()
        self.assertEqual(dice.random(), mirror.random())


class Commands(unittest.TestCase):
    def test_deputies_are_multiplied_by_the_share(self):
        household = SimpleNamespace(directors_extra=4.0)
        module_harness.build(Workforce, views={"legacy_acting_household": household}).scale_deputies(ScaleDeputies(0.5))
        self.assertEqual(household.directors_extra, 2.0)

    def test_the_log_of_staff_lost_is_asked_with_the_cause_and_the_headcount_before(self):
        asked = []
        workforce = module_harness.build(Workforce)
        workforce.labour = SimpleNamespace(log_staff_reduction=lambda cause, before: asked.append((cause, before)))
        workforce.report_staff_reduction(ReportStaffReduction("a sack", {"smith": 3.0}))
        self.assertEqual(asked, [("a sack", {"smith": 3.0})])

    def test_a_trade_spread_notes_the_year_first_taught_and_that_it_became_endemic(self):
        household = SimpleNamespace(trade_introduced_year={}, trades_endemic=set())
        workforce = module_harness.build(Workforce, views={"legacy_acting_household": household})
        workforce.note_trade_spread(NoteTradeSpread("smith", introduced_year=120))
        self.assertEqual((household.trade_introduced_year, household.trades_endemic), ({"smith": 120}, set()))
        workforce.note_trade_spread(NoteTradeSpread("smith", endemic=True))
        self.assertEqual((household.trade_introduced_year, household.trades_endemic), ({"smith": 120}, {"smith"}))

    def test_setting_the_staff_of_a_trade_resyncs_the_hour_pools_after(self):
        calls = []
        workforce = module_harness.build(Workforce)
        workforce.labour = SimpleNamespace(set_employed=lambda trade, headcount: calls.append(("set", trade, headcount)),
                                           resync_pools=lambda: calls.append(("resync",)))
        workforce.set_employed(SetEmployed("smith", 3.0))
        self.assertEqual(calls, [("set", "smith", 3.0), ("resync",)])

    def test_pressing_labour_presses_the_markets_trade(self):
        pressed = []
        workforce = module_harness.build(Workforce)
        workforce.labour = SimpleNamespace(market=SimpleNamespace(press=lambda trade, hours: pressed.append((trade, hours))))
        workforce.press_labour(PressLabour("smith", 500.0))
        self.assertEqual(pressed, [("smith", 500.0)])


class WageFallback(unittest.TestCase):
    """A household with no work and thin means sells idle hours for wages, unless it is played by hand."""

    def fallback(self, remaining, manual=False, capital=0.0, active=(), pays=(10.0, 4.0), held=None):
        sold = []
        household = SimpleNamespace(capital=capital)
        workforce = module_harness.build(Workforce, views={
            "legacy_acting_household": household, "automation": {"manual": manual}, "living_cost": lambda *args: 100.0,
            "legacy_projects": SimpleNamespace(active=dict.fromkeys(active)), "held_trade": lambda: held})
        workforce.labour = SimpleNamespace(
            effective_scholars=lambda: 2.0, work_for_wages=lambda trade, hours: sold.append((trade, hours)) or (1.0, None),
            wage_for_hours=lambda trade, hours: pays[0] if trade == "scholar" else pays[1])
        return workforce.take_wage_fallback(TakeWageFallback(remaining)), sold

    def test_idle_hours_are_sold_up_to_the_ceiling_and_leave_the_year_less_unspent(self):
        left, sold = self.fallback(WAGE_FALLBACK_MAX_HOURS + 500.0)
        self.assertEqual(sold, [("scholar", WAGE_FALLBACK_MAX_HOURS)])
        self.assertEqual(left, 500.0)

    def test_a_seat_played_by_hand_and_a_token_amount_of_hours_sell_nothing(self):
        self.assertEqual(self.fallback(WAGE_FALLBACK_MAX_HOURS, manual=True), (WAGE_FALLBACK_MAX_HOURS, []))
        self.assertEqual(self.fallback(WAGE_FALLBACK_MIN_HOURS), (WAGE_FALLBACK_MIN_HOURS, []))

    def test_a_household_with_cash_and_projects_in_hand_sells_nothing(self):
        capital = 100.0 * WAGE_FALLBACK_LIVING_COST_YEARS + 1.0
        self.assertEqual(self.fallback(500.0, capital=capital, active=("a",)), (500.0, []))

    def test_hours_are_not_moved_from_a_standing_job_that_pays_better(self):
        self.assertEqual(self.fallback(500.0, pays=(3.0, 3.0), held="artisan"), (500.0, []))


class HoursYear(unittest.TestCase):
    def test_the_year_ends_with_its_breakdown_kept_the_ledger_closed_and_the_tallies_reset(self):
        closed = []
        household = SimpleNamespace(wage_hours_this_year=120.04, teaching_hours_this_year=30.0, relocation_hours_this_year=None,
                                    supervision_hours_this_year=7.0, contract_hours={"smith": 40.0}, hours_this_year=None)
        workforce = module_harness.build(Workforce, views={"legacy_acting_household": household})
        workforce.labour = SimpleNamespace(director_pool=lambda: 2000.04, close_wage_year=lambda: closed.append(dict(
            kept=household.hours_this_year, wage=household.wage_hours_this_year)))
        workforce.close_hours_year(CloseHoursYear(pool=1500.0, remaining=-3.0, remaining_after_projects=400.0, hours_effective_total=800.04))
        self.assertEqual(household.hours_this_year, {
            "available": 2000.0, "wage_work": 120.0, "teaching": 30.0, "moving": 0.0, "supervising": 7.0,
            "offered_to_projects": 1100.0, "effective_on_projects": 800.0, "unused": 0.0})
        self.assertEqual([entry["kept"] is household.hours_this_year for entry in closed], [True])   # kept before the ledger closed
        self.assertEqual((household.contract_hours, household.teaching_hours_this_year, household.relocation_hours_this_year,
                          household.supervision_hours_this_year), ({}, 0.0, 0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
