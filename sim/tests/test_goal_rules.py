"""The rules of goals and win conditions, each a function of plain values (sim/seats/goal_rules.py)."""

QUICK_TOPIC = True

import unittest

from sim.seats import goal_rules
from sim.seats.api import win_condition_met


class WinConditionMet(unittest.TestCase):

    def test_a_greater_or_equal_condition_is_met_at_its_target_and_above_not_below(self):
        condition = {"op": ">=", "value": 0.2}
        self.assertTrue(win_condition_met(condition, 0.2))
        self.assertTrue(win_condition_met(condition, 0.9))
        self.assertFalse(win_condition_met(condition, 0.1999))

    def test_a_less_or_equal_condition_is_met_at_its_target_and_below_not_above(self):
        condition = {"op": "<=", "value": 5}
        self.assertTrue(win_condition_met(condition, 5))
        self.assertTrue(win_condition_met(condition, 0))
        self.assertFalse(win_condition_met(condition, 5.01))

    def test_any_other_comparison_is_never_met(self):
        self.assertFalse(win_condition_met({"op": "==", "value": 1}, 1))


class AttributeSource(unittest.TestCase):

    def test_a_count_the_people_hold_is_read_as_a_float(self):
        self.assertEqual(goal_rules.staff_number("slaves", {"slaves": 4, "employees": {}}), 4.0)

    def test_a_key_that_is_not_a_count_is_refused(self):
        for key in ("employees", "unheld", None, 3):
            with self.assertRaises(ValueError):
                goal_rules.staff_number(key, {"slaves": 4, "employees": {"smith": 1.0}})


class Measurements(unittest.TestCase):

    def test_a_source_with_no_generation_anywhere_has_no_share(self):
        self.assertEqual(goal_rules.generation_share(0.0, 0.0), 0.0)
        self.assertEqual(goal_rules.generation_share(40.0, 10.0), 0.25)

    def test_relief_is_what_is_cut_of_the_harm(self):
        self.assertEqual(goal_rules.epidemic_relief(0.75), 0.25)

    def test_the_anatomy_of_a_generation_goal_names_the_source_and_the_total_then_the_current_value(self):
        rows = goal_rules.measurement_rows("generation_share", "coal", {"sources_kw": {"coal": 3.0}, "total_kw": 12.0}, [], None, 0.25)
        self.assertEqual(rows, [("this source", 3.0, "kW"), ("all generation", 12.0, "kW"), ("current", 0.25, "fraction")])

    def test_the_anatomy_of_an_epidemic_goal_lists_what_cuts_the_harm(self):
        rows = goal_rules.measurement_rows(None, None, None, [{"label": "boiled water", "factor": 0.8}], "epidemic_relief", 0.2)
        self.assertEqual([row[0] for row in rows], ["boiled water", "current"])
        self.assertAlmostEqual(rows[0][1], 0.2)


class GoalYears(unittest.TestCase):

    def test_the_formal_goal_records_its_year_when_reached(self):
        years = {}
        self.assertEqual(goal_rules.record_year(years, None, "c", "c", 1000), 1000)
        self.assertEqual(years, {"c": 1000})

    def test_a_node_that_is_not_the_goal_records_nothing(self):
        years = {}
        self.assertIsNone(goal_rules.record_year(years, None, "c", "a", 1000))
        self.assertEqual(years, {})

    def test_the_goal_year_stays_the_first_one(self):
        years = {"c": 1000}
        self.assertEqual(goal_rules.record_year(years, 1000, "c", "c", 1010), 1000)
        self.assertEqual(years, {"c": 1000})


class DescribeWinCondition(unittest.TestCase):
    LABELS = {"literacy_general": "literacy reaches %s"}

    def test_the_nodes_own_description_wins(self):
        node = {"win_condition": {"description": "own words", "metric": "literacy_general", "value": 0.2}}
        self.assertEqual(goal_rules.describe_win_condition(node, self.LABELS), "own words")

    def test_a_labelled_metric_fills_its_template_with_the_target_percentage(self):
        node = {"win_condition": {"metric": "literacy_general", "op": ">=", "value": 0.25}}
        self.assertEqual(goal_rules.describe_win_condition(node, self.LABELS), "literacy reaches 25%")

    def test_a_metric_with_no_label_states_the_comparison(self):
        node = {"win_condition": {"metric": "mystery", "op": ">=", "value": 2}}
        self.assertEqual(goal_rules.describe_win_condition(node, self.LABELS), "a measurement (mystery >= 2) is met")


if __name__ == "__main__":
    unittest.main()
