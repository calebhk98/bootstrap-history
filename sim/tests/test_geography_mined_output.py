"""What a country's deposits have yielded before a start year, derived from the deposit rows."""

QUICK_TOPIC = True

import unittest

from sim.geography import queries, resources_mined
from sim.tests.test_geography_resources import small_map


class MinedOutputTests(unittest.TestCase):
    def setUp(self):
        self.world_map = small_map()
        self.share = queries.parameter_value("resources_working_share_per_year", self.world_map)

    def test_a_dated_deposit_yields_its_share_of_the_endowment_each_year_it_was_worked(self):
        result = queries.mined_before(["b2"], "gold", -100, self.world_map)
        [working] = result["workings"]
        self.assertEqual(working["id"], "old_vein")
        self.assertAlmostEqual(working["output_per_year"], 1000.0 * self.share)
        self.assertEqual(working["years_worked"], 200.0)
        self.assertEqual(working["years_since_last_output"], 0.0)

    def test_a_deposit_is_worked_out_after_the_years_its_share_takes_and_then_ages(self):
        late = int(-300 + 3.0 / self.share)
        working = queries.mined_before(["b2"], "gold", late, self.world_map)["workings"][0]
        self.assertAlmostEqual(working["years_worked"], 1.0 / self.share)
        self.assertAlmostEqual(working["years_since_last_output"], late - (-300 + 1.0 / self.share))

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
