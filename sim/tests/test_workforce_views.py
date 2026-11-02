"""The views the workforce module publishes, on a module built over plain values for the views it reads."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.tests import module_harness
from sim.workforce import rules
from sim.workforce.module import Workforce
from sim.workforce.api import WorkforceSeat


class CountAfterBleed(unittest.TestCase):
    def test_a_count_above_the_floor_falls_by_the_share(self):
        self.assertEqual(rules.count_after_bleed(10.0, 3.0, 0.25), 7.5)

    def test_a_count_stops_falling_at_the_floor(self):
        self.assertEqual(rules.count_after_bleed(4.0, 3.0, 0.5), 3.0)

    def test_a_count_below_the_floor_is_left_as_it_was(self):
        self.assertEqual(rules.count_after_bleed(0.0, 3.0, 0.5), 0.0)
        self.assertEqual(rules.count_after_bleed(1.5, 3.0, 0.5), 1.5)


class WageMaterials(unittest.TestCase):
    def test_the_staple_comes_first_then_each_trades_tool_materials_once_in_trade_order(self):
        registry = {"smith": {"tool_basket": ["iron_kg", "charcoal_kg"]}, "carpenter": {"tool_basket": ["iron_kg", "timber_kg"]},
                    "idler": {}}
        self.assertEqual(rules.wage_materials_of("wheat_kg", registry), ["wheat_kg", "iron_kg", "timber_kg", "charcoal_kg"])

    def test_no_trades_leave_the_staple_alone(self):
        self.assertEqual(rules.wage_materials_of("wheat_kg", {}), ["wheat_kg"])


class StaffViews(unittest.TestCase):
    def test_the_staff_view_is_the_household_people_by_class(self):
        seat = WorkforceSeat(employees={"smith": 2.0}, scholars=3.0, artisans=4.0, slaves=5)
        workforce = module_harness.build(Workforce, seat=seat)
        self.assertEqual(workforce.staff(), {"employees": {"smith": 2.0}, "scholars": 3.0, "artisans": 4.0, "directors_extra": 0.0,
                                             "slaves": 5, "freedmen": 0, "manumitted_total": 0, "reserve_craftsmen": 0,
                                             "reserve_scholars": 0})

    def test_the_trade_spread_view_names_the_absent_trades_sorted_and_the_live_records(self):
        household = SimpleNamespace(trades_created={"smith"}, trades_endemic=set(), trade_introduced_year={"smith": 90})
        workforce = module_harness.build(Workforce, seat=household, views={"trades_absent": frozenset({"b", "a"})})
        spread = workforce.trade_spread()
        self.assertEqual(spread["absent"], ["a", "b"])
        self.assertIs(spread["created"], household.trades_created)
        self.assertIs(spread["introduced_year"], household.trade_introduced_year)


class WorkingDay(unittest.TestCase):
    def test_no_work_declaring_a_working_day_leaves_the_convention(self):
        from sim.unit_conversions import HOURS_PER_PERSON_YEAR
        workforce = module_harness.build(Workforce, views={"mechanic": {"working_day": {}}})
        self.assertEqual(workforce.hours_per_person_year(), HOURS_PER_PERSON_YEAR)


if __name__ == "__main__":
    unittest.main()
