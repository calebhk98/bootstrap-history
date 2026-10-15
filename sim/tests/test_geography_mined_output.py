"""What a country's deposits have yielded before a start year, derived from the deposit rows."""

QUICK_TOPIC = True

import math
import unittest

from sim.geography import queries, resources_mined
from sim.tests.test_geography_resources import small_map


class MinedOutputTests(unittest.TestCase):
    def setUp(self):
        self.world_map = small_map()
        self.share = queries.parameter_value("resources_working_share_per_year", self.world_map)

    def test_a_dated_deposit_yields_its_share_of_what_it_holds_each_year_it_was_worked(self):
        result = queries.mined_before(["b2"], "gold", -100, self.world_map)
        [working] = result["workings"]
        self.assertEqual(working["id"], "old_vein")
        self.assertAlmostEqual(working["mined_share"], 1.0 - math.exp(-self.share * 200.0))
        self.assertAlmostEqual(working["output_per_year"], 1000.0 * self.share * (1.0 - working["mined_share"]))
        self.assertEqual(working["years_worked"], 200.0)
        self.assertEqual(working["years_since_last_output"], 0.0)

    def test_a_deposit_worked_for_ages_is_drawn_down_but_never_closed_by_a_horizon(self):
        ages = int(-300 + 3.0 / self.share)
        working = queries.mined_before(["b2"], "gold", ages, self.world_map)["workings"][0]
        self.assertAlmostEqual(working["mined_share"], 1.0 - math.exp(-3.0 - 0.0), places=3)
        self.assertLess(working["mined_share"], 1.0)
        self.assertEqual(working["years_since_last_output"], 0.0)

    def test_a_historical_rate_from_the_data_sets_how_much_is_gone(self):
        slow = 0.00025     # tonnes a year, a quarter of a thousandth of the 1 tonne of gold the vein holds
        working = queries.mined_before(["b2"], "gold", 700, self.world_map, {"old_vein": slow})["workings"][0]
        self.assertAlmostEqual(working["mined_share"], 1.0 - math.exp(-0.00025 * 1000.0))
        fast = queries.mined_before(["b2"], "gold", 700, self.world_map, {"old_vein": slow * 40.0})["workings"][0]
        self.assertGreater(fast["mined_share"], working["mined_share"])

    def test_nothing_is_counted_before_the_deposit_was_first_worked(self):
        result = queries.mined_before(["b2"], "gold", -400, self.world_map)
        self.assertEqual(result["workings"], [])
        self.assertEqual(result["unworked"], ["old_vein"])

    def test_a_deposit_with_no_working_date_is_named_not_guessed(self):
        result = queries.mined_before(["a1"], "gold", 0, self.world_map)
        self.assertEqual(result["workings"], [])
        self.assertEqual(result["unworked"], ["big_gold"])

    def test_a_resource_with_no_deposit_in_the_tiles_yields_nothing_and_says_so(self):
        result = queries.mined_before(["a3"], "gold", 0, self.world_map)
        self.assertEqual(result, {"workings": [], "unworked": [], "deposits_in_tiles": 0, "unit": "kg"})


if __name__ == "__main__":
    unittest.main()
