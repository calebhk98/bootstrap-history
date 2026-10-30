"""`LabourAllocationMixin.farm_share_of_hours`: once the society has booked hours, the farm share is farming's share of the hours
booked. Called on a stand-in carrying only the booked hours; no game. (Before any are booked it is the food balance's workforce
over the working-age population, which the food rules' own tests cover.)"""
import types
import unittest

from sim.labour.labour_allocation import FARM_TRADE, LabourAllocationMixin

QUICK_TOPIC = True


def labour_with(hours):
    return types.SimpleNamespace(_world=types.SimpleNamespace(
        society=types.SimpleNamespace(society_labour_hours=hours)))


class FarmShareOfHoursTests(unittest.TestCase):
    def test_the_farm_share_is_farming_hours_over_all_hours_booked(self):
        share = LabourAllocationMixin.farm_share_of_hours(labour_with({FARM_TRADE: 300.0, "smith": 100.0, "weaver": 100.0}))
        self.assertAlmostEqual(share, 0.6)

    def test_a_society_that_books_only_farming_is_all_farm(self):
        self.assertEqual(LabourAllocationMixin.farm_share_of_hours(labour_with({FARM_TRADE: 5.0})), 1.0)

    def test_a_society_that_books_no_farming_has_no_farm_share(self):
        self.assertEqual(LabourAllocationMixin.farm_share_of_hours(labour_with({FARM_TRADE: 0.0, "smith": 4.0})), 0.0)


if __name__ == "__main__":
    unittest.main()
