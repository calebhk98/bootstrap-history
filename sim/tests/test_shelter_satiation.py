"""Shelter is bounded per head by a multiple of its climate floor (Complaint 619): a household with money left
does not build wall without end, which sent clay, stone and fuel to brickworks and quarries in quantities no
pre-industrial dwelling stock explains. Value tests on the need's units and on the shipped data."""

QUICK_TOPIC = True

import json
import os
import unittest

from sim.world import demand, need_basket, need_demand

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
POPULATION = 1_000_000.0
MEAN_INCOME = 550.0
SHELTER_FLOOR_PER_HEAD = 0.05

PRODUCTION = {
    "wheat_kg": {"outputs": {"wheat_kg": 100.0}, "inputs": {}, "labour_hours": {"labourer": 10.0}},
    "brick_1000": {"outputs": {"brick_1000": 1.0}, "inputs": {}, "labour_hours": {"labourer": 10.0}},
    "tool_kg": {"outputs": {"tool_kg": 1.0}, "inputs": {}, "labour_hours": {"labourer": 10.0}},
}


def needs(multiple):
    shelter = {"surplus_budget_share": 0.6, "subsistence_per_capita_per_year": SHELTER_FLOOR_PER_HEAD}
    if multiple is not None:
        shelter["satiation_multiple_of_floor"] = multiple
    return {
        "needs": {"food": {"surplus_budget_share": 0.2, "subsistence_per_capita_per_year": 200.0},
                  "tools": {"surplus_budget_share": 0.2}, "shelter": shelter},
        "goods": {"wheat_kg": {"satisfies": {"food": 1.0}},
                  "tool_kg": {"satisfies": {"tools": 1.0}},
                  "brick_1000": {"satisfies": {"shelter": 1.0}}},
    }


def shelter_units_per_head(multiple):
    model = need_demand.NeedDemandModel(
        needs(multiple), PRODUCTION, demand.income_bins(POPULATION, MEAN_INCOME), satiate=True)
    quantities = model.final_demand({"wheat_kg": 0.5, "tool_kg": 5.0, "brick_1000": 1.0})
    return quantities["brick_1000"] / POPULATION


class ShelterSatiation(unittest.TestCase):

    def test_shelter_units_stop_at_the_multiple_of_the_floor(self):
        free = shelter_units_per_head(None)
        self.assertGreater(free, 3.0 * SHELTER_FLOOR_PER_HEAD)     # the fixture's budget would buy more
        self.assertAlmostEqual(shelter_units_per_head(3.0), 3.0 * SHELTER_FLOOR_PER_HEAD, places=9)

    def test_a_limit_above_what_the_budget_buys_does_not_bind(self):
        self.assertAlmostEqual(shelter_units_per_head(1e6), shelter_units_per_head(None), places=9)

    def test_the_limit_follows_the_floor_of_the_tile(self):
        data = needs(3.0)
        basket = need_basket.make_basket(data, PRODUCTION)
        self.assertAlmostEqual(need_basket.satiation_limit(basket, "shelter", 0.2), 0.6, places=9)
        self.assertIsNone(need_basket.satiation_limit(basket, "tools", 0.2))

    def test_shipped_shelter_declares_a_bounded_multiple_with_its_basis(self):
        with open(os.path.join(ROOT, "data", "world", "needs.json"), encoding="utf-8") as handle:
            shelter = json.load(handle)["needs"]["shelter"]
        self.assertGreaterEqual(shelter["satiation_multiple_of_floor"], 1.0)
        self.assertLessEqual(shelter["satiation_multiple_of_floor"], 10.0)
        self.assertTrue(shelter["satiation_basis"])


if __name__ == "__main__":
    unittest.main()
