"""Joint-process cost is split by demand-derived value, not by mass.

Joint-process cost is split by demand-derived value, not by mass.
"""
import unittest

from sim import joint_allocation, simulator, solve_prices
from sim.world import demand


def joint_entry():
    return {"outputs": {"main_kg": 1000.0, "gem_kg": 1.0}, "inputs": {},
            "labour_hours": {"labourer": 100.0}}


class AllocateJointCostTests(unittest.TestCase):

    def test_without_anchors_the_split_is_unchanged(self):
        outputs = {"main_kg": 1000.0, "gem_kg": 1.0}
        prices = joint_allocation.allocate_joint_cost(outputs, {}, 100.0)
        self.assertAlmostEqual(prices["main_kg"], prices["gem_kg"])

    def test_an_anchored_minor_output_takes_a_demand_sized_share(self):
        outputs = {"main_kg": 1000.0, "gem_kg": 1.0}
        prices = joint_allocation.allocate_joint_cost(
            outputs, {}, 100.0, {"gem_kg": 500.0})
        self.assertGreater(prices["gem_kg"], 100.0 * prices["main_kg"])
        recovered = sum(prices[name] * quantity for name, quantity in outputs.items())
        self.assertAlmostEqual(recovered, 100.0)

    def test_the_main_output_price_does_not_feed_back_into_its_own_share(self):
        outputs = {"main_kg": 1000.0, "gem_kg": 1.0}
        cheap = joint_allocation.allocate_joint_cost(
            outputs, {"main_kg": 0.0001}, 100.0, {"gem_kg": 500.0})
        dear = joint_allocation.allocate_joint_cost(
            outputs, {"main_kg": 99.0}, 100.0, {"gem_kg": 500.0})
        self.assertAlmostEqual(cheap["main_kg"], dear["main_kg"])


class WasteOutputTests(unittest.TestCase):
    """Outputs only have to recover the batch together, not one mass share each."""

    outputs = {"metal_kg": 1.0, "slag_kg": 1000.0}

    def test_a_bulk_waste_carries_far_less_than_its_mass_share(self):
        # Slag is nearly all the mass and worth almost nothing; the metal is the reason for the batch.
        prices = joint_allocation.allocate_joint_cost(
            self.outputs, {}, 100.0, {"metal_kg": 500.0, "slag_kg": 0.001})
        slag_share = prices["slag_kg"] * 1000.0 / 100.0
        self.assertLess(slag_share, 0.01)
        self.assertGreater(prices["metal_kg"], 50.0)

    def test_the_batch_cost_is_still_recovered_exactly(self):
        prices = joint_allocation.allocate_joint_cost(
            self.outputs, {}, 100.0, {"metal_kg": 500.0, "slag_kg": 0.001})
        recovered = sum(prices[name] * quantity for name, quantity in self.outputs.items())
        self.assertAlmostEqual(recovered, 100.0)


class UnitConsistentFallbackTests(unittest.TestCase):
    """Without anchors the split is by mass, so a gram is not priced like a kilogram."""

    def test_one_kilogram_of_each_output_costs_the_same(self):
        outputs = {"nickel_kg": 1000.0, "platinum_g": 40.0}
        prices = joint_allocation.allocate_joint_cost(outputs, {}, 100.0)
        self.assertAlmostEqual(prices["nickel_kg"], prices["platinum_g"] * 1000.0)

    def test_the_batch_cost_is_recovered(self):
        outputs = {"nickel_kg": 1000.0, "platinum_g": 40.0}
        prices = joint_allocation.allocate_joint_cost(outputs, {}, 100.0)
        self.assertAlmostEqual(
            sum(prices[name] * quantity for name, quantity in outputs.items()), 100.0)

    def test_an_unanchored_output_beside_an_anchored_one_is_mass_valued(self):
        outputs = {"nickel_kg": 1000.0, "platinum_g": 40.0, "gem_kg": 1.0}
        prices = joint_allocation.allocate_joint_cost(outputs, {}, 100.0, {"gem_kg": 500.0})
        self.assertAlmostEqual(prices["nickel_kg"], prices["platinum_g"] * 1000.0)

    def test_an_output_with_no_mass_unit_is_flagged_and_left_out_of_the_split(self):
        outputs = {"metal_kg": 10.0, "heat_mj": 50.0}
        with self.assertWarns(UserWarning):
            prices = joint_allocation.allocate_joint_cost(outputs, {}, 100.0)
        self.assertAlmostEqual(prices["metal_kg"] * 10.0, 100.0)
        self.assertEqual(prices["heat_mj"], 0.0)


class CapAnchorsTests(unittest.TestCase):

    def test_an_anchor_is_capped_at_the_direct_route_price(self):
        capped = joint_allocation.cap_anchors(
            {"gem_kg": 900.0, "other_kg": 5.0}, {"gem_kg": 70.0})
        self.assertEqual(capped, {"gem_kg": 70.0, "other_kg": 5.0})

    def test_a_cheaper_anchor_is_kept(self):
        self.assertEqual(
            joint_allocation.cap_anchors({"gem_kg": 10.0}, {"gem_kg": 70.0}),
            {"gem_kg": 10.0})

    def test_no_anchors_stays_none(self):
        self.assertIsNone(joint_allocation.cap_anchors(None, {"gem_kg": 70.0}))


class DemandAnchorsTests(unittest.TestCase):

    def anchors(self, supply_kg):
        bins = demand.income_bins(1_000_000.0, 500.0)
        basket = (demand.FOOD, demand.Good("gem_kg", 0.0, 0.70))
        return joint_allocation.DemandAnchors(bins, basket, {"gem_kg": supply_kg})

    def test_scarcer_supply_gives_a_higher_anchor(self):
        prices = {"wheat_kg": 0.5}
        scarce = self.anchors(10.0).prices(prices)["gem_kg"]
        plentiful = self.anchors(1000.0).prices(prices)["gem_kg"]
        self.assertGreater(scarce, plentiful)

    def test_a_good_with_no_known_supply_gets_no_anchor(self):
        anchors = joint_allocation.DemandAnchors(
            demand.income_bins(1_000_000.0, 500.0),
            (demand.FOOD, demand.Good("gem_kg", 0.0, 0.70)), {})
        self.assertEqual(anchors.prices({"wheat_kg": 0.5}), {})

    def test_a_direct_route_caps_the_anchor_in_a_solved_joint_recipe(self):
        # Direct route: 1 kg gem costs 20 hours; the joint smelt's anchor says 400.
        entries = {"smelt": joint_entry(), "direct": {
            "outputs": {"gem_kg": 1.0}, "inputs": {},
            "labour_hours": {"labourer": 20.0}}}
        producers = solve_prices.build_producers_index(entries)
        anchors = self.anchors(50.0)
        anchors.prices = lambda _prices: {"gem_kg": 400.0}
        prices, iterations, _r, _c = solve_prices.solve(
            entries, producers, {"main_kg", "gem_kg"}, {"labourer": 1.0},
            demand_anchors=anchors)
        # Uncapped, the smelt alone would price gem near 80 per kg.
        self.assertLessEqual(prices["gem_kg"], 20.0)
        self.assertLess(iterations, solve_prices.MAXIMUM_ITERATIONS)

    def test_a_custom_anchor_reaches_a_solved_joint_recipe(self):
        entries = {"smelt": joint_entry()}
        wages = {"labourer": 1.0}
        producers = solve_prices.build_producers_index(entries)
        resolvable = {"main_kg", "gem_kg"}
        # wheat is not solved here, so anchor prices come from a stub.
        anchors = self.anchors(50.0)
        anchors.prices = lambda _prices: {"gem_kg": 400.0}
        prices, _i, _r, _c = solve_prices.solve(
            entries, producers, resolvable, wages, demand_anchors=anchors)
        self.assertGreater(prices["gem_kg"], 100.0 * prices["main_kg"])


def solve_ungated(with_anchors):
    entries, _duplicates = solve_prices.load_production()
    _tree, prices_json, _nodes, _wages, _goods = simulator.load()
    wages = solve_prices.wage_ratios_by_trade(prices_json)
    producers = solve_prices.build_producers_index(entries)
    rent = solve_prices.rent_hours_per_kg_by_ore_material(entries, wages)
    resolvable = solve_prices.compute_resolvable_materials(
        entries, producers, rent_hours_per_kg_by_material=rent)
    anchors = joint_allocation.build_demand_anchors() if with_anchors else None
    prices, iterations, residual, chosen = solve_prices.solve(
        entries, producers, resolvable, wages,
        rent_hours_per_kg_by_material=rent, demand_anchors=anchors)
    unanchored = solve_prices.minor_joint_byproducts_are_unanchored(
        entries, chosen, prices, wages, rent_hours_per_kg_by_material=rent,
        demand_anchors=anchors)
    solved = SolvedRun(prices, unanchored, iterations, residual, chosen, entries)
    return solved


class SolvedRun:

    def __init__(self, prices, unanchored, iterations, residual, chosen, entries):
        self.prices = prices
        self.unanchored = unanchored
        self.iterations = iterations
        self.residual = residual
        self.chosen = chosen
        self.entries = entries


class RealDataJointSmeltTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        before = solve_ungated(False)
        after = solve_ungated(True)
        cls.before, cls.unanchored_before = before.prices, before.unanchored
        cls.after, cls.unanchored_after = after.prices, after.unanchored
        cls.solved = after

    def test_solver_converges_without_oscillating(self):
        self.assertLess(self.solved.iterations, solve_prices.MAXIMUM_ITERATIONS)
        self.assertLess(self.solved.residual, solve_prices.CONVERGENCE_TOLERANCE)

    def test_every_joint_recipe_recovers_its_batch_cost_exactly(self):
        _tree, prices_json, _nodes, _wages, _goods = simulator.load()
        wages = solve_prices.wage_ratios_by_trade(prices_json)
        rent = solve_prices.rent_hours_per_kg_by_ore_material(self.solved.entries, wages)
        checked = 0
        for material, recipe_id in self.solved.chosen.items():
            entry = self.solved.entries[recipe_id]
            if len(entry.get("outputs") or {}) < 2 or material not in entry["outputs"]:
                continue
            costed = solve_prices.recipe_cost_and_allocation(
                recipe_id, entry, self.after, wages, rent_hours_per_kg_by_material=rent)
            if costed is None:
                continue
            total_cost, output_prices = costed
            recovered = sum(output_prices[name] * quantity
                            for name, quantity in entry["outputs"].items())
            self.assertAlmostEqual(recovered, total_cost, places=6, msg=recipe_id)
            checked += 1
        self.assertGreater(checked, 0)

    def test_no_solved_price_is_negative_or_vanishing_next_to_its_input(self):
        for material in ("lead_kg", "silver_kg"):
            self.assertGreater(self.after[material], 0.0)
        # Lead is at least what its galena costs per kg of ore, before any other cost.
        self.assertGreater(self.after["lead_kg"], self.after["galena_kg"])

    def test_lead_pays_for_its_own_galena(self):
        self.assertGreater(self.after["lead_kg"], 1.77 * self.after["galena_kg"])

    def test_mass_split_prices_silver_like_lead(self):
        self.assertAlmostEqual(self.before["silver_kg"], self.before["lead_kg"], places=6)

    def test_silver_is_far_dearer_than_lead_per_kg_once_demand_is_used(self):
        self.assertGreater(self.after["silver_kg"], 50.0 * self.after["lead_kg"])

    def test_silver_is_no_longer_reported_as_unanchored(self):
        self.assertIn("silver_kg", self.unanchored_before)
        self.assertNotIn("silver_kg", self.unanchored_after)

    def test_byproducts_with_no_demand_curve_stay_flagged(self):
        for material in ("platinum_g", "germanium_g", "indium_g", "coal_tar_kg"):
            self.assertIn(material, self.unanchored_after)


if __name__ == "__main__":
    unittest.main()
