"""The commands the workforce module applies, on a module built over plain household figures, and the rules they call."""
QUICK_TOPIC = True

import random
import unittest
from types import SimpleNamespace

from sim.tests import module_harness
from sim.workforce import rules as workforce_rules
from sim.workforce.api import NoteTradeSpread, PressLabour, ReportStaffReduction, ScaleDeputies, SetEmployed
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


if __name__ == "__main__":
    unittest.main()
