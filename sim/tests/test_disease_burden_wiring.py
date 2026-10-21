"""The disease burden a civilisation lives under is 1.0 less the share of the disease technologies' weight it holds
(`burden_from_holdings`): tested on built weights. The seam through a real game (that the burden reaches the population
step) is in test_disease_burden_wiring_scenario.py."""
QUICK_TOPIC = True

import unittest

from sim.engine.disease_burden import burden_from_holdings
from sim.world import demography

WEIGHTS = {"water": 0.05, "sanitation": 0.05, "germ_theory": 0.03, "vaccine": 0.02}
NONE_HELD = {}
ALL_HELD = {tech_id: 1.0 for tech_id in WEIGHTS}


class BurdenFromHoldings(unittest.TestCase):
    def test_holding_none_is_the_pre_industrial_burden(self):
        self.assertEqual(burden_from_holdings(WEIGHTS, NONE_HELD), demography.PRE_INDUSTRIAL_DISEASE_BURDEN)

    def test_holding_one_technology_lowers_burden_by_exactly_its_own_share(self):
        self.assertAlmostEqual(burden_from_holdings(WEIGHTS, {"germ_theory": 1.0}), 1.0 - 0.03 / sum(WEIGHTS.values()), places=12)

    def test_holding_every_technology_leaves_no_burden(self):
        self.assertAlmostEqual(burden_from_holdings(WEIGHTS, ALL_HELD), 0.0, places=12)

    def test_a_work_that_serves_a_share_of_the_people_counts_for_that_share(self):
        half = burden_from_holdings(WEIGHTS, {"water": 0.5})
        self.assertAlmostEqual(half, 1.0 - 0.025 / sum(WEIGHTS.values()), places=12)
        self.assertGreater(half, burden_from_holdings(WEIGHTS, {"water": 1.0}))

    def test_a_technology_outside_the_set_does_not_move_the_burden(self):
        self.assertEqual(burden_from_holdings(WEIGHTS, {"crop_rotation": 1.0}), demography.PRE_INDUSTRIAL_DISEASE_BURDEN)

    def test_the_burden_is_clamped_to_zero_one(self):
        self.assertEqual(burden_from_holdings(WEIGHTS, {"water": 5.0}), 0.0)
        self.assertEqual(burden_from_holdings(WEIGHTS, {"water": -5.0}), 1.0)

    def test_with_no_weight_at_all_the_burden_stays_pre_industrial(self):
        self.assertEqual(burden_from_holdings({}, {}), demography.PRE_INDUSTRIAL_DISEASE_BURDEN)
        self.assertEqual(burden_from_holdings({"water": 0.0}, {"water": 1.0}), demography.PRE_INDUSTRIAL_DISEASE_BURDEN)


if __name__ == "__main__":
    unittest.main()
