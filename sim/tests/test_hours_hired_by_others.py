"""Rule tests (Complaint 556): the hours other employers hired are counted apart from the producers' own."""
import unittest

from sim.economy import hours_hired_by_others, workforce_settle
from sim.economy.market_memory import market_key


class HoursHiredByOthersTests(unittest.TestCase):
    def test_a_producers_hours_that_made_no_run_are_not_other_buyers_hours(self):
        hired = {"producer:glass@a": 100.0, "state": 20.0}
        self.assertEqual(hours_hired_by_others.beyond_producers(hired, {"producer:glass@a"}), 20.0)

    def test_no_other_employer_means_nothing(self):
        self.assertEqual(hours_hired_by_others.beyond_producers({"producer:glass@a": 100.0}, {"producer:glass@a"}), 0.0)

    def test_the_hours_wanted_add_only_the_others_hired_in_the_trades_the_area_holds(self):
        wanted = workforce_settle.add_others_hired({("area", "glassblower"): 30.0},
                                                   {"area": {"glassblower": [1.0], "smith": [1.0]}},
                                                   {market_key("glassblower", "area"): 20.0})
        self.assertEqual(wanted, {("area", "glassblower"): 50.0, ("area", "smith"): 0.0})


if __name__ == "__main__":
    unittest.main()
