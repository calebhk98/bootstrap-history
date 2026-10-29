"""The views the workforce module publishes, on a module built over plain values for the views it reads."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.demography.api import DEFAULT_POPULATION_100AD, POP_SCALE_FLOOR
from sim.tests import module_harness
from sim.workforce import rules
from sim.workforce.constants import WAGE_SCARCITY_ELASTICITY
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


class WageIndex(unittest.TestCase):
    def index(self, pop_scale, population=DEFAULT_POPULATION_100AD, base=1.0):
        return module_harness.build(Workforce, views={
            "opening_wage_index": base, "civilisation": {"population": population}, "pop_scale": pop_scale}).wage_index()

    def test_a_nation_at_its_unshocked_trend_pays_the_base_index(self):
        self.assertEqual(self.index(1.0), 1.0)
        self.assertEqual(self.index(1.0, base=1.5), 1.5)

    def test_a_nation_below_its_trend_pays_more_in_proportion_to_the_shortfall(self):
        self.assertAlmostEqual(self.index(0.5), 1.0 + WAGE_SCARCITY_ELASTICITY * 0.5)

    def test_a_nation_above_its_trend_pays_the_base_index(self):
        self.assertEqual(self.index(1.4), 1.0)

    def test_the_trend_is_the_civilisations_people_against_the_default_and_never_below_the_floor(self):
        self.assertEqual(self.index(2.0, population=2 * DEFAULT_POPULATION_100AD), 1.0)
        self.assertAlmostEqual(self.index(1.0, population=2 * DEFAULT_POPULATION_100AD), 1.0 + WAGE_SCARCITY_ELASTICITY * 0.5)
        self.assertEqual(self.index(POP_SCALE_FLOOR, population=0.0), 1.0)

    def test_the_terms_name_the_base_index_and_the_elasticity(self):
        terms = module_harness.build(Workforce, views={"opening_wage_index": 1.2}).wage_index_terms()
        self.assertEqual(terms, {"base": 1.2, "elasticity": WAGE_SCARCITY_ELASTICITY})


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
