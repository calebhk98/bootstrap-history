"""Complaint 556: the crew hours the opening's carriage will bid bound the people seeded into carriage-only trades
(carriage_opening_hours: the average haul's hours per tonne, times the tonnes an area's merchants carry)."""
QUICK_TOPIC = True

import unittest

from sim.economy import carriage_opening_hours as rule


class MeanHoursPerTonneTests(unittest.TestCase):
    def test_the_hours_of_each_trade_are_averaged_over_the_hauls_a_haul_without_the_trade_counting_zero(self):
        mean = rule.mean_hours_per_tonne([{"carter": 4.0, "sailor": 2.0}, {"carter": 2.0}])
        self.assertEqual(mean, {"carter": 3.0, "sailor": 1.0})

    def test_no_hauls_need_no_hours(self):
        self.assertEqual(rule.mean_hours_per_tonne([]), {})


class CrewHoursByAreaTests(unittest.TestCase):
    def test_an_areas_hours_are_its_tonnes_times_the_hours_a_tonne_needs_there(self):
        found = rule.crew_hours_by_area({"port": 10.0, "inland": 5.0}, {"port": {"sailor": 3.0, "carter": 0.5}, "inland": {"carter": 2.0}})
        self.assertEqual(found, {"port": {"sailor": 30.0, "carter": 5.0}, "inland": {"carter": 10.0}})

    def test_an_area_with_no_tonnes_or_no_hours_per_tonne_asks_nothing(self):
        self.assertEqual(rule.crew_hours_by_area({"port": 0.0, "far": 4.0}, {"port": {"sailor": 3.0}}), {})


if __name__ == "__main__":
    unittest.main()
