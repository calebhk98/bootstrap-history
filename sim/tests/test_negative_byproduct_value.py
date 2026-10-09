"""Complaints/309: a glutted waste by-product prices at minus its disposal cost, and the batch is still recovered."""

QUICK_TOPIC = True

import math
import unittest

from sim.engine import disposal_cost, joint_allocation, joint_floor, solve_prices, solve_prices_core

OUTPUTS = {"tar_kg": 1000.0, "charcoal_kg": 2500.0}
BATCH_COST = 760.0
TAR_DISPOSAL_COST_PER_UNIT = 0.005


def allocate(tar_anchor, tar_disposal_cost):
    return joint_allocation.allocate_joint_cost(
        OUTPUTS, {}, BATCH_COST, {"tar_kg": tar_anchor, "charcoal_kg": 4.0},
        disposal_cost_by_material={"tar_kg": tar_disposal_cost})


class GlutPriceTests(unittest.TestCase):

    def test_a_glutted_byproduct_prices_at_minus_its_disposal_cost(self):
        prices = allocate(1e-9, TAR_DISPOSAL_COST_PER_UNIT)
        self.assertAlmostEqual(prices["tar_kg"], -TAR_DISPOSAL_COST_PER_UNIT)

    def test_the_batch_is_recovered_and_the_main_product_pays_the_disposal(self):
        prices = allocate(1e-9, TAR_DISPOSAL_COST_PER_UNIT)
        free = allocate(1e-9, 0.0)
        recovered = sum(prices[name] * quantity for name, quantity in OUTPUTS.items())
        self.assertAlmostEqual(recovered, BATCH_COST)
        self.assertGreater(prices["charcoal_kg"], free["charcoal_kg"])

    def test_a_byproduct_with_demand_above_its_disposal_cost_keeps_a_positive_price(self):
        prices = allocate(0.5, TAR_DISPOSAL_COST_PER_UNIT)
        self.assertGreater(prices["tar_kg"], 0.0)

    def test_an_unanchored_output_is_never_priced_below_zero(self):
        prices = joint_allocation.allocate_joint_cost(
            OUTPUTS, {}, BATCH_COST, {}, disposal_cost_by_material={"tar_kg": TAR_DISPOSAL_COST_PER_UNIT})
        self.assertGreaterEqual(prices["tar_kg"], 0.0)

    def test_a_negative_reference_value_does_not_corrupt_the_split(self):
        shares = joint_allocation._split_by_value(OUTPUTS, {"tar_kg": -3.0, "charcoal_kg": 4.0}, BATCH_COST)
        self.assertTrue(all(price >= 0.0 for price in shares.values()))
        self.assertAlmostEqual(sum(shares[name] * OUTPUTS[name] for name in OUTPUTS), BATCH_COST)

    def test_the_bound_lifts_a_price_below_it_and_charges_the_others(self):
        prices = {"tar_kg": -1.0, "charcoal_kg": 0.5}
        lifted = joint_floor.bound_to_disposal_cost(prices, OUTPUTS, {"tar_kg": 0.002})
        self.assertAlmostEqual(lifted["tar_kg"], -0.002)
        self.assertAlmostEqual(
            sum(lifted[name] * OUTPUTS[name] for name in OUTPUTS),
            sum(prices[name] * OUTPUTS[name] for name in OUTPUTS))


class DisposalCostTests(unittest.TestCase):

    def test_it_grows_with_distance_to_the_dump(self):
        near = disposal_cost.disposal_cost_hours_per_kilogram(distance_kilometres=1.0)
        far = disposal_cost.disposal_cost_hours_per_kilogram(distance_kilometres=10.0)
        self.assertGreater(far, near)

    def test_it_grows_with_the_land_rent(self):
        cheap = disposal_cost.disposal_cost_hours_per_kilogram(land_rent_hours_per_hectare_year=10.0)
        dear = disposal_cost.disposal_cost_hours_per_kilogram(land_rent_hours_per_hectare_year=1000.0)
        self.assertGreater(dear, cheap)

    def test_it_falls_with_bulk_density_and_heap_height(self):
        rent = 1000.0
        loose = disposal_cost.disposal_cost_hours_per_kilogram(rent, bulk_density=500.0)
        dense = disposal_cost.disposal_cost_hours_per_kilogram(rent, bulk_density=2000.0)
        low = disposal_cost.disposal_cost_hours_per_kilogram(rent, heap_height=1.0)
        high = disposal_cost.disposal_cost_hours_per_kilogram(rent, heap_height=6.0)
        self.assertGreater(loose, dense)
        self.assertGreater(low, high)

    def test_land_is_capitalised_at_the_interest_rate(self):
        patient = disposal_cost.disposal_cost_hours_per_kilogram(1000.0, interest_rate=0.02)
        impatient = disposal_cost.disposal_cost_hours_per_kilogram(1000.0, interest_rate=0.2)
        self.assertGreater(patient, impatient)

    def test_the_cost_is_per_unit_of_the_material(self):
        costs = disposal_cost.disposal_cost_by_material(["tar_kg", "gold_g"], {}, 0.05)
        self.assertAlmostEqual(costs["tar_kg"] / costs["gold_g"], 1000.0)

    def test_only_joint_outputs_get_a_bound(self):
        entries = {"kiln": {"outputs": {"tar_kg": 1.0, "charcoal_kg": 2.0}},
                   "mill": {"outputs": {"flour_kg": 1.0}}}
        self.assertEqual(disposal_cost.joint_output_materials(entries), ["charcoal_kg", "tar_kg"])


class SolverTests(unittest.TestCase):

    def test_a_negative_price_still_moving_is_not_converged(self):
        prices, residual = solve_prices_core._solve_round_update_prices(
            ["waste_kg"], {"waste_kg": -0.1}, {"waste_kg": [(-0.5, "dump")]}, 0.5, {})
        self.assertAlmostEqual(prices["waste_kg"], -0.3)
        self.assertGreater(residual, 0.1)

    def test_the_bound_applies_before_the_cheapest_candidate_is_chosen(self):
        prices, _residual = solve_prices_core._solve_round_update_prices(
            ["waste_kg"], {"waste_kg": 0.0}, {"waste_kg": [(-5.0, "glut"), (1.0, "other")]}, 1.0, {},
            disposal_floor={"waste_kg": -0.25})
        self.assertAlmostEqual(prices["waste_kg"], -0.25)

    def test_a_solved_glut_prices_at_minus_the_disposal_cost_and_the_batch_is_recovered(self):
        entries = {"kiln": {"outputs": {"tar_kg": 1000.0, "charcoal_kg": 2500.0}, "inputs": {},
                            "labour_hours": {"labourer": 100.0}}}

        class GluttedDemand:
            def prices(self, _prices):
                return {"tar_kg": 1e-12, "charcoal_kg": 2.0}

        prices, _i, _r, _c = solve_prices.solve(
            entries, solve_prices.build_producers_index(entries), {"tar_kg", "charcoal_kg"},
            {"labourer": 1.0}, demand_anchors=GluttedDemand())
        expected = disposal_cost.disposal_cost_by_material(["tar_kg"], {})["tar_kg"]
        self.assertLess(prices["tar_kg"], 0.0)
        self.assertAlmostEqual(prices["tar_kg"], -expected, places=9)
        self.assertTrue(math.isfinite(prices["charcoal_kg"]))
        self.assertAlmostEqual(
            prices["tar_kg"] * 1000.0 + prices["charcoal_kg"] * 2500.0, 100.0, places=4)


if __name__ == "__main__":
    unittest.main()
