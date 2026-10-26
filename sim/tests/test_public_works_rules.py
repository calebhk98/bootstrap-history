"""Complaint 640: the free press, grain dole, lit working day and schooling rules (`public_works_rules`) on built inputs."""

QUICK_TOPIC = True

import unittest

from sim.defence_stores.api import rules as defence_rules
from sim.engine.public_works_rules import (extra_lit_hours, legitimacy_share, printing_boosted_flow,
                                           schooling_flow, working_hours_per_year)

relief_kcal_per_day = defence_rules.relief_kcal_per_day

FLOOR, CEILING = 0.5, 1.25


class Legitimacy(unittest.TestCase):
    def test_with_no_work_declaring_it_the_state_keeps_all_its_capacity(self):
        self.assertEqual(legitimacy_share(1.0, FLOOR, CEILING), 1.0)

    def test_a_free_press_wears_the_share_down_and_a_licensed_one_raises_it(self):
        self.assertAlmostEqual(legitimacy_share(1.0 - 0.02 * 4.0 ** 0.5, FLOOR, CEILING), 0.96)
        self.assertGreater(legitimacy_share(1.1, FLOOR, CEILING), 1.0)

    def test_however_many_presses_the_state_keeps_the_floor_and_praise_stops_at_the_ceiling(self):
        self.assertEqual(legitimacy_share(-1.0e6, FLOOR, CEILING), FLOOR)
        self.assertEqual(legitimacy_share(1.0e6, FLOOR, CEILING), CEILING)


class GrainDole(unittest.TestCase):
    def test_a_dole_hands_out_its_kilograms_as_calories_a_day(self):
        self.assertAlmostEqual(relief_kcal_per_day([(365000.0, 3000.0)], 365.0), 3.0e6)

    def test_more_works_hand_out_more_and_none_hands_out_nothing(self):
        one = relief_kcal_per_day([(365000.0, 3000.0)], 365.0)
        self.assertAlmostEqual(relief_kcal_per_day([(365000.0, 3000.0), (365000.0, 3000.0)], 365.0), 2.0 * one)
        self.assertEqual(relief_kcal_per_day([], 365.0), 0.0)


class LitWorkingDay(unittest.TestCase):
    def test_lights_over_half_the_people_add_half_the_lit_hours(self):
        self.assertAlmostEqual(extra_lit_hours([(4.0, 0.5)]), 2.0)

    def test_no_open_lights_add_nothing_and_works_add_up(self):
        self.assertEqual(extra_lit_hours([]), 0.0)
        self.assertAlmostEqual(extra_lit_hours([(4.0, 0.5), (1.0, 1.0)]), 3.0)

    def test_a_longer_day_gives_a_longer_year_in_the_same_proportion(self):
        self.assertAlmostEqual(working_hours_per_year(2500.0, 0.0, 10.0), 2500.0)
        self.assertAlmostEqual(working_hours_per_year(2500.0, 2.0, 10.0), 3000.0)


class Schooling(unittest.TestCase):
    SCHOOLS = [(1.0, None), (0.5, ("literacy_general",)), (0.25, ("literacy_elite",))]

    def test_the_whole_flow_is_every_open_school_alike(self):
        self.assertAlmostEqual(schooling_flow(self.SCHOOLS, None, False), 1.75)

    def test_a_school_that_names_no_group_teaches_both(self):
        self.assertAlmostEqual(schooling_flow(self.SCHOOLS[:1], "literacy_general", False), 1.0)
        self.assertAlmostEqual(schooling_flow(self.SCHOOLS[:1], "literacy_elite", False), 1.0)

    def test_a_school_for_the_many_adds_to_the_many_and_not_to_the_lettered(self):
        self.assertAlmostEqual(schooling_flow(self.SCHOOLS[:2], "literacy_general", False), 1.5)
        self.assertAlmostEqual(schooling_flow(self.SCHOOLS[:2], "literacy_elite", False), 1.0)

    def test_a_college_adds_to_the_lettered_and_not_to_the_many(self):
        self.assertAlmostEqual(schooling_flow([self.SCHOOLS[0], self.SCHOOLS[2]], "literacy_elite", False), 1.25)
        self.assertAlmostEqual(schooling_flow([self.SCHOOLS[0], self.SCHOOLS[2]], "literacy_general", False), 1.0)

    def test_where_the_original_school_is_shut_nobody_is_taught(self):
        self.assertEqual(schooling_flow(self.SCHOOLS, None, True), 0.0)
        self.assertEqual(schooling_flow(self.SCHOOLS, "literacy_general", True), 0.0)

    def test_printing_speeds_the_same_effort_but_zero_stays_zero(self):
        self.assertAlmostEqual(printing_boosted_flow(2.0, 0.5, 0.4), 2.0 * 1.2)
        self.assertEqual(printing_boosted_flow(0.0, 0.5, 0.4), 0.0)
        self.assertEqual(printing_boosted_flow(2.0, 0.5, 0.0), 2.0)


if __name__ == "__main__":
    unittest.main()
