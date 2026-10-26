"""Joint-process cost is split by value at reference prices, and by mass where there is none (Complaints/507).

The split reads no demand: a reference price comes from the caller, else from the cheapest sole-output route
that makes the good, else the output is valued by its mass.
"""
QUICK_TOPIC = True

import functools
import unittest
import warnings

from sim import simulator
from sim.prices import rent_standin, solve_prices, joint_allocation


def joint_entry():
    return {"outputs": {"main_kg": 1000.0, "gem_kg": 1.0}, "inputs": {},
            "labour_hours": {"labourer": 100.0}}


class AllocateJointCostTests(unittest.TestCase):

    def test_without_references_the_split_is_by_mass(self):
        outputs = {"main_kg": 1000.0, "gem_kg": 1.0}
        prices = joint_allocation.allocate_joint_cost(outputs, 100.0)
        self.assertAlmostEqual(prices["main_kg"], prices["gem_kg"])

    def test_a_referenced_minor_output_takes_a_share_sized_by_its_reference(self):
        outputs = {"main_kg": 1000.0, "gem_kg": 1.0}
        prices = joint_allocation.allocate_joint_cost(outputs, 100.0, {"gem_kg": 500.0})
        self.assertGreater(prices["gem_kg"], 100.0 * prices["main_kg"])
        recovered = sum(prices[name] * quantity for name, quantity in outputs.items())
        self.assertAlmostEqual(recovered, 100.0)

    def test_a_dearer_reference_takes_more_of_the_batch(self):
        outputs = {"main_kg": 1000.0, "gem_kg": 1.0}
        cheap = joint_allocation.allocate_joint_cost(outputs, 100.0, {"gem_kg": 50.0})
        dear = joint_allocation.allocate_joint_cost(outputs, 100.0, {"gem_kg": 500.0})
        self.assertGreater(dear["gem_kg"], cheap["gem_kg"])
        self.assertLess(dear["main_kg"], cheap["main_kg"])

    def test_the_split_follows_the_references_in_proportion(self):
        outputs = {"a_kg": 2.0, "b_kg": 3.0}
        prices = joint_allocation.allocate_joint_cost(outputs, 100.0, {"a_kg": 10.0, "b_kg": 5.0})
        self.assertAlmostEqual(prices["a_kg"] * 2.0, 100.0 * 20.0 / 35.0)
        self.assertAlmostEqual(prices["b_kg"] * 3.0, 100.0 * 15.0 / 35.0)

    def test_a_single_output_takes_the_whole_batch(self):
        self.assertAlmostEqual(joint_allocation.allocate_joint_cost({"only_kg": 4.0}, 100.0)["only_kg"], 25.0)


class WasteOutputTests(unittest.TestCase):
    """Outputs only have to recover the batch together, not one mass share each."""

    outputs = {"metal_kg": 1.0, "slag_kg": 1000.0}

    def test_a_bulk_waste_carries_far_less_than_its_mass_share(self):
        # Slag is nearly all the mass and worth almost nothing; the metal is the reason for the batch.
        prices = joint_allocation.allocate_joint_cost(
            self.outputs, 100.0, {"metal_kg": 500.0, "slag_kg": 0.001})
        slag_share = prices["slag_kg"] * 1000.0 / 100.0
        self.assertLess(slag_share, 0.01)
        self.assertGreater(prices["metal_kg"], 50.0)

    def test_the_batch_cost_is_still_recovered_exactly(self):
        prices = joint_allocation.allocate_joint_cost(
            self.outputs, 100.0, {"metal_kg": 500.0, "slag_kg": 0.001})
        recovered = sum(prices[name] * quantity for name, quantity in self.outputs.items())
        self.assertAlmostEqual(recovered, 100.0)


class WasteTests(unittest.TestCase):
    outputs = {"main_kg": 1000.0, "ash_kg": 500.0}

    def test_a_recorded_waste_with_no_reference_carries_no_share(self):
        prices = joint_allocation.allocate_joint_cost(self.outputs, 100.0, waste_materials={"ash_kg"})
        self.assertEqual(prices["ash_kg"], joint_allocation.UNPRICED_WASTE_VALUE)
        self.assertAlmostEqual(prices["main_kg"] * 1000.0, 100.0)

    def test_a_reference_for_a_waste_wins(self):
        prices = joint_allocation.allocate_joint_cost(
            self.outputs, 100.0, {"ash_kg": 0.05}, waste_materials={"ash_kg"})
        self.assertGreater(prices["ash_kg"], 0.0)
        self.assertAlmostEqual(prices["main_kg"] * 1000.0 + prices["ash_kg"] * 500.0, 100.0)

    def test_it_is_not_split_by_mass(self):
        self.assertEqual(joint_allocation.outputs_split_by_mass(self.outputs, {}, {"ash_kg"}), ["main_kg"])


class UnitConsistentFallbackTests(unittest.TestCase):
    """Without references the split is by mass, so a gram is not priced like a kilogram."""

    def test_one_kilogram_of_each_output_costs_the_same(self):
        outputs = {"nickel_kg": 1000.0, "platinum_g": 40.0}
        prices = joint_allocation.allocate_joint_cost(outputs, 100.0)
        self.assertAlmostEqual(prices["nickel_kg"], prices["platinum_g"] * 1000.0)

    def test_the_batch_cost_is_recovered(self):
        outputs = {"nickel_kg": 1000.0, "platinum_g": 40.0}
        prices = joint_allocation.allocate_joint_cost(outputs, 100.0)
        self.assertAlmostEqual(
            sum(prices[name] * quantity for name, quantity in outputs.items()), 100.0)

    def test_an_output_with_no_reference_beside_a_referenced_one_is_mass_valued(self):
        outputs = {"nickel_kg": 1000.0, "platinum_g": 40.0, "gem_kg": 1.0}
        prices = joint_allocation.allocate_joint_cost(outputs, 100.0, {"gem_kg": 500.0})
        self.assertAlmostEqual(prices["nickel_kg"], prices["platinum_g"] * 1000.0)

    def test_an_output_with_no_mass_unit_and_no_reference_is_flagged_and_left_out_of_the_split(self):
        outputs = {"metal_kg": 10.0, "heat_mj": 50.0}
        with self.assertWarns(UserWarning):
            prices = joint_allocation.allocate_joint_cost(outputs, 100.0)
        self.assertAlmostEqual(prices["metal_kg"] * 10.0, 100.0)
        self.assertEqual(prices["heat_mj"], 0.0)

    def test_an_output_with_no_mass_unit_takes_its_reference(self):
        outputs = {"metal_kg": 10.0, "heat_mj": 50.0}
        prices = joint_allocation.allocate_joint_cost(outputs, 100.0, {"heat_mj": 1.0, "metal_kg": 1.0})
        self.assertAlmostEqual(prices["heat_mj"] * 50.0, 100.0 * 50.0 / 60.0)


class SoleRouteReferenceTests(unittest.TestCase):
    """In a solve, an output a sole-output route also makes is worth what that route costs."""

    def test_a_direct_route_is_the_reference_of_a_joint_output(self):
        # Direct route: 1 kg gem costs 20 hours. Valued by mass the joint smelt would price gem near 0.1.
        entries = {"smelt": joint_entry(), "direct": {
            "outputs": {"gem_kg": 1.0}, "inputs": {},
            "labour_hours": {"labourer": 20.0}}}
        producers = solve_prices.build_producers_index(entries)
        prices, iterations, _residual, _chosen = solve_prices.solve(
            entries, producers, {"main_kg", "gem_kg"}, {"labourer": 1.0})
        self.assertLessEqual(prices["gem_kg"], 20.0)
        self.assertGreater(prices["gem_kg"], 10.0)
        self.assertLess(iterations, solve_prices.MAXIMUM_ITERATIONS)
        recovered = prices["main_kg"] * 1000.0 + prices["gem_kg"] * 1.0
        self.assertAlmostEqual(recovered, 100.0, places=4)

    def test_a_reference_the_caller_gives_beats_the_direct_route(self):
        entries = {"smelt": joint_entry(), "direct": {
            "outputs": {"gem_kg": 1.0}, "inputs": {},
            "labour_hours": {"labourer": 20.0}}}
        producers = solve_prices.build_producers_index(entries)
        prices, _i, _r, _c = solve_prices.solve(
            entries, producers, {"main_kg", "gem_kg"}, {"labourer": 1.0},
            reference_price_by_material={"gem_kg": 0.001})
        # gem is cheapest by the direct route (20) or the joint one; with a tiny reference the joint one is cheap
        self.assertLess(prices["gem_kg"], 1.0)

    def test_with_no_direct_route_the_joint_outputs_are_priced_alike_per_kilogram(self):
        entries = {"smelt": joint_entry()}
        producers = solve_prices.build_producers_index(entries)
        prices, _i, _r, _c = solve_prices.solve(entries, producers, {"main_kg", "gem_kg"}, {"labourer": 1.0})
        self.assertAlmostEqual(prices["gem_kg"], prices["main_kg"])


@functools.lru_cache(maxsize=None)
def solve_ungated():
    """One full solve per run; callers must not mutate it. Warnings raised during the solve are kept."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        solved = _solve_ungated_once()
    solved.warnings = [str(item.message) for item in caught]
    return solved


def _solve_ungated_once():
    entries, _duplicates = solve_prices.load_production()
    _tree, prices_json, _nodes, _wages, _goods = simulator.load()
    wages = solve_prices.wage_ratios_by_trade(prices_json)
    producers = solve_prices.build_producers_index(entries)
    rent = rent_standin.rent_hours_per_kg_by_ore_material(entries, wages)
    resolvable = solve_prices.compute_resolvable_materials(
        entries, producers, rent_hours_per_kg_by_material=rent)
    prices, iterations, residual, chosen = solve_prices.solve(
        entries, producers, resolvable, wages, rent_hours_per_kg_by_material=rent)
    by_mass = solve_prices.minor_joint_byproducts_split_by_mass(
        entries, chosen, prices, wages, rent_hours_per_kg_by_material=rent)
    return SolvedRun(prices, by_mass, iterations, residual, chosen, entries)


class SolvedRun:

    def __init__(self, prices, by_mass, iterations, residual, chosen, entries):
        self.prices = prices
        self.by_mass = by_mass
        self.iterations = iterations
        self.residual = residual
        self.chosen = chosen
        self.entries = entries


class RealDataJointSmeltTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.solved = solve_ungated()
        cls.prices = cls.solved.prices

    def test_solver_converges_without_oscillating(self):
        self.assertLess(self.solved.iterations, solve_prices.MAXIMUM_ITERATIONS)
        self.assertLess(self.solved.residual, solve_prices.CONVERGENCE_TOLERANCE)

    def test_every_joint_recipe_recovers_its_batch_cost_exactly(self):
        _tree, prices_json, _nodes, _wages, _goods = simulator.load()
        wages = solve_prices.wage_ratios_by_trade(prices_json)
        rent = rent_standin.rent_hours_per_kg_by_ore_material(self.solved.entries, wages)
        checked = 0
        for material, recipe_id in self.solved.chosen.items():
            entry = self.solved.entries[recipe_id]
            if len(entry.get("outputs") or {}) < 2 or material not in entry["outputs"]:
                continue
            costed = solve_prices.recipe_cost_and_allocation(
                recipe_id, entry, self.prices, wages, rent_hours_per_kg_by_material=rent)
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
            self.assertGreater(self.prices[material], 0.0)
        # Lead is at least what its galena costs per kg of ore, before any other cost.
        self.assertGreater(self.prices["lead_kg"], self.prices["galena_kg"])

    def test_lead_pays_for_its_own_galena(self):
        self.assertGreater(self.prices["lead_kg"], 1.77 * self.prices["galena_kg"])

    def test_silver_is_far_dearer_than_lead_per_kg_because_a_direct_route_values_it(self):
        self.assertGreater(self.prices["silver_kg"], 50.0 * self.prices["lead_kg"])

    def test_silver_is_not_split_by_mass(self):
        self.assertNotIn("silver_kg", self.solved.by_mass)

    def test_byproducts_with_no_reference_stay_flagged(self):
        for material in ("germanium_g", "indium_g"):
            self.assertIn(material, self.solved.by_mass)

    def test_a_recorded_waste_with_no_reference_is_worth_nothing_and_not_split_by_mass(self):
        for material in ("wood_tar_kg", "coal_tar_kg"):
            self.assertNotIn(material, self.solved.by_mass)
            self.assertLess(abs(self.prices[material]), 1e-9, material)

    def test_the_main_product_of_a_run_with_a_waste_carries_the_whole_batch(self):
        # the retort makes charcoal and tar from the wood a charcoal burner uses; tar worth nothing leaves
        # charcoal at what burning it alone costs
        entries = self.solved.entries
        burn = next(entry for entry in entries.values() if list(entry["outputs"]) == ["charcoal_kg"]
                    and "wood_kg" in (entry.get("inputs") or {}))
        per_kilogram_of_wood = burn["outputs"]["charcoal_kg"] / burn["inputs"]["wood_kg"]
        retort = next(entry for entry in entries.values() if "wood_tar_kg" in entry["outputs"])
        self.assertAlmostEqual(retort["outputs"]["charcoal_kg"] / retort["inputs"]["wood_kg"], per_kilogram_of_wood)

    def test_two_minor_byproducts_of_one_run_with_no_reference_are_priced_alike_per_kilogram(self):
        self.assertAlmostEqual(self.prices["germanium_g"], self.prices["indium_g"])


if __name__ == "__main__":
    unittest.main()
