"""Pins the fix for Complaints/32's own follow-up finding: `sim/solve_prices.py`
printed "Rent on extracted materials is fixed at 0.0 this round (RENT_IS_ZERO)"
on every run, although `sim/world/deposits.py` sat unimported next to it with a
complete, tested Ricardian rent model (extensive margin, intensive margin,
sinking cost, byproducts). `recipe_cost_and_allocation` now takes a
`rent_hours_per_kg_by_material` table, and `rent_hours_per_kg_by_ore_material`
builds it from `deposits.find_marginal_deposit` for the six metals
`data/production/` represents as a standalone EXTRACTED ore material (iron,
copper, tin, lead, silver, mercury - see RENT_BEARING_ORE_MATERIALS and RENT
ON EXTRACTED MATERIALS in the module docstring for why gold is the seventh
metal `deposits.py` covers and is not among these six).

Written as unittest.TestCase against solve_prices directly, like
test_price_solver_cycles.py and test_price_solver_era_gate.py, so it does not
drag in the engine. A few tests use real `data/production/` and
`data/world/deposits.json` data (an integration check that the real tables
actually wire together and stay convergent); the rest build tiny synthetic
entries, like test_price_solver_era_gate.py's own `entry()` helper, so the
mechanism itself is pinned independent of any future edit to those data
files (which this task does not own).
"""
import unittest
from unittest import mock

from sim import solve_prices
from sim.world import deposits


class RentIsZeroByDefaultTests(unittest.TestCase):
    """Backward compatibility: a caller that passes no rent table at all -
    every call site in this file before this task, and any future caller
    that has no opinion about rent - must see exactly the old RENT_IS_ZERO
    behaviour, not a crash and not a surprise nonzero charge.
    """

    def test_no_rent_table_means_zero_rent(self):
        entry = {"outputs": {"thing_kg": 1000.0}, "inputs": {},
                "labour_hours": {"labourer": 10.0}}
        with_table, without_table = (
            solve_prices.recipe_cost_and_allocation(
                "thing_kg", entry, {}, {"labourer": 1.0}),
            solve_prices.recipe_cost_and_allocation(
                "thing_kg", entry, {}, {"labourer": 1.0},
                rent_hours_per_kg_by_material=None))
        self.assertEqual(with_table, without_table)
        total_cost, _prices = with_table
        self.assertEqual(total_cost, 10.0)  # labour only, no rent

    def test_an_empty_rent_table_also_means_zero_rent(self):
        entry = {"outputs": {"thing_kg": 1000.0}, "inputs": {},
                "labour_hours": {"labourer": 10.0}}
        total_cost, _prices = solve_prices.recipe_cost_and_allocation(
            "thing_kg", entry, {}, {"labourer": 1.0},
            rent_hours_per_kg_by_material={})
        self.assertEqual(total_cost, 10.0)

    def test_a_material_not_named_in_the_table_still_gets_zero_rent(self):
        # The whole point of RENT ON EXTRACTED MATERIALS: forest timber,
        # quarried stone and every metal deposits.py has no named-deposit
        # list for stay at exactly zero, unconditionally, even when SOME
        # other material in the same solve now carries a real rent.
        entry = {"outputs": {"stone_kg": 1000.0}, "inputs": {},
                "labour_hours": {"labourer": 4.0}}
        total_cost, _prices = solve_prices.recipe_cost_and_allocation(
            "stone_kg", entry, {}, {"labourer": 1.0},
            rent_hours_per_kg_by_material={"iron_ore_kg": 5.0})
        self.assertEqual(total_cost, 4.0)


class RentIsAddedCorrectlyTests(unittest.TestCase):
    """The mechanism itself, on synthetic entries, independent of the real
    tables - see the module's own top docstring.
    """

    def test_rent_is_added_per_kg_of_the_named_output(self):
        entry = {"outputs": {"ore_kg": 1000.0}, "inputs": {},
                "labour_hours": {"miner": 20.0}}
        total_cost, output_prices = solve_prices.recipe_cost_and_allocation(
            "ore_kg", entry, {}, {"miner": 1.0},
            rent_hours_per_kg_by_material={"ore_kg": 0.25})
        # 20 h labour + 0.25 h/kg * 1000 kg rent = 270 h for the batch.
        self.assertEqual(total_cost, 20.0 + 0.25 * 1000.0)
        self.assertAlmostEqual(output_prices["ore_kg"], total_cost / 1000.0)

    def test_rent_on_a_joint_output_recipe_is_summed_across_outputs(self):
        # Not a real shape in data/production/ today (no rent-bearing ore
        # has a byproduct of its own), but recipe_cost_and_allocation must
        # not assume single-output, the same discipline the rest of this
        # function already keeps for inputs, labour and energy.
        entry = {"outputs": {"ore_a_kg": 1000.0, "ore_b_kg": 10.0},
                "inputs": {}, "labour_hours": {"miner": 20.0}}
        total_cost, _prices = solve_prices.recipe_cost_and_allocation(
            "ore_a_kg", entry, {"ore_a_kg": 1.0, "ore_b_kg": 1.0},
            {"miner": 1.0},
            rent_hours_per_kg_by_material={"ore_a_kg": 0.1, "ore_b_kg": 2.0})
        self.assertEqual(total_cost, 20.0 + 0.1 * 1000.0 + 2.0 * 10.0)


class RentHoursPerKgByOreMaterialTests(unittest.TestCase):
    """rent_hours_per_kg_by_ore_material itself: the function that closes
    (or, honestly, cuts - see the module docstring's own TEMPORARY HEURISTIC
    paragraph) the demand-determines-the-margin loop.
    """

    def _minimal_entries(self, ore_labour_hours=10.0, ore_output_kg=1000.0,
                        ore_per_metal=50.0, metal_output_kg=1000.0):
        return {
            "test_ore_kg": {
                "outputs": {"test_ore_kg": ore_output_kg}, "inputs": {},
                "labour_hours": {"miner": ore_labour_hours},
                "extracted_from": "ore deposit"},
            "test_metal_kg": {
                "outputs": {"test_metal_kg": metal_output_kg},
                "inputs": {"test_ore_kg": ore_per_metal * metal_output_kg / 1000.0},
                "labour_hours": {"furnaceman": 1.0}},
        }

    def test_rent_is_never_negative_even_when_the_deposit_price_is_cheap(self):
        # A metal whose marginal-deposit price (from deposits.py) comes out
        # BELOW what the zero-rent recipe already implies must floor at
        # 0.0, not go negative - rent is a surplus, never a discount. Faked
        # via a real table entry (copper) with find_marginal_deposit
        # patched to return a price far below copper_ore_kg's own labour-
        # only cost.
        entries = dict(solve_prices.load_production()[0])  # real data
        wage_by_trade = {"miner": 1.0, "furnaceman": 1.0, "labourer": 1.0,
                         "smith": 1.0}
        cheap_outcome = deposits.MarginalOutcome(
            quantity_demanded_tonnes_per_year=1.0,
            price_at_margin_labour_hours_per_kg=1e-9,
            marginal_deposit=None, allocations=(),
            quantity_supplied_tonnes_per_year=1.0,
            unmet_demand_tonnes_per_year=0.0)
        with mock.patch.object(deposits, "find_marginal_deposit",
                               return_value=cheap_outcome):
            rent = solve_prices.rent_hours_per_kg_by_ore_material(
                entries, wage_by_trade)
        self.assertIn("copper_ore_kg", rent)
        self.assertEqual(rent["copper_ore_kg"], 0.0)

    def test_a_metal_missing_its_dominant_recipe_is_skipped_not_guessed(self):
        # If neither of a metal's candidate recipes survives whatever
        # entries this call was given (an era gate this task's own docstring
        # warns about for iron), that ore is left out of the returned table
        # entirely rather than assigned an invented number.
        entries = self._minimal_entries()
        del entries["test_metal_kg"]
        rent = solve_prices.rent_hours_per_kg_by_ore_material(
            {"iron_ore_kg": entries["test_ore_kg"]},  # only the ore, no smelter
            {"miner": 1.0})
        self.assertEqual(rent, {})

    def test_the_real_solve_produces_a_sane_rent_table(self):
        # Integration check against the committed data/production/ and
        # data/world/deposits.json - no book-price comparison, no pinned
        # numbers (both files are owned elsewhere and can change), only the
        # structural properties this mechanism promises.
        production_entries, duplicates = solve_prices.load_production()
        self.assertEqual(duplicates, [])
        _tree, prices_json, _nodes, _wages, _goods = __import__(
            "simulator").load()
        wage_by_trade = solve_prices.wage_ratios_by_trade(prices_json)
        rent = solve_prices.rent_hours_per_kg_by_ore_material(
            production_entries, wage_by_trade)

        # All six named ores resolve in the ungated (full) solve - none of
        # their dominant/candidate recipes are missing from the real data.
        self.assertEqual(set(rent), set(solve_prices.RENT_BEARING_ORE_MATERIALS))
        for material, rent_per_kg in rent.items():
            self.assertGreaterEqual(rent_per_kg, 0.0, material)
        # At least one metal's margin is genuinely pushed by the fixed
        # empire_output_100ad quantity demanded - a rent of exactly zero
        # everywhere would mean the wiring runs but never actually bites.
        self.assertTrue(any(value > 0.0 for value in rent.values()), rent)

    def test_gold_is_not_in_the_table(self):
        # gold_kg folds extraction and amalgamation into one recipe with no
        # extracted_from ore stage of its own (see WHAT THIS DOES NOT REACH
        # in the module docstring) - the seventh metal deposits.py covers,
        # deliberately left out of RENT_BEARING_ORE_MATERIALS.
        self.assertNotIn("gold_kg", solve_prices.RENT_BEARING_ORE_MATERIALS)
        self.assertNotIn("gold", [metal for metal, _recipes in
                                  solve_prices.RENT_BEARING_ORE_MATERIALS.values()])


class IronFallsBackToTheAvailableSmeltingRouteTests(unittest.TestCase):
    """Iron is the one metal with two ore-consuming recipes at different
    ore-to-metal ratios (pig_iron_kg's blast furnace, iron_bloom_kg's
    bloomery), and `--civ rome_100ad` gates pig_iron_kg out entirely
    (blast_furnace is not a Roman technology) while leaving iron_bloom_kg
    available - exactly the scenario this task's own VERIFY step runs. A
    single fixed recipe id would have silently left iron at zero rent for
    every Roman-era gated solve; the tuple-of-candidates fallback must not
    regress to that.
    """

    def test_pig_iron_is_preferred_when_both_are_present(self):
        preferred, fallback = solve_prices.RENT_BEARING_ORE_MATERIALS["iron_ore_kg"][1]
        self.assertEqual(preferred, "pig_iron_kg")
        self.assertEqual(fallback, "iron_bloom_kg")

    def test_the_real_roman_gate_actually_exercises_the_fallback(self):
        # Pinning the PRECONDITION this fallback exists for: if a future
        # edit to data/civilizations/rome_100ad.json or data/production/
        # ever gave Rome the blast furnace, this test would start failing
        # here (not silently) and say so, rather than the fallback path
        # quietly going untested.
        production_entries, _duplicates = solve_prices.load_production()
        reached = solve_prices.load_starting_technologies("rome_100ad")
        available, _unreached, _unclassified = solve_prices.techniques_available_to(
            production_entries, reached)
        self.assertNotIn("pig_iron_kg", available,
                         "rome_100ad now holds the blast furnace - the "
                         "RENT_BEARING_ORE_MATERIALS fallback this test "
                         "guards is no longer exercised by this civilization")
        self.assertIn("iron_bloom_kg", available)

    def test_iron_ore_still_gets_a_rent_entry_under_the_roman_gate(self):
        production_entries, _duplicates = solve_prices.load_production()
        reached = solve_prices.load_starting_technologies("rome_100ad")
        available, _unreached, _unclassified = solve_prices.techniques_available_to(
            production_entries, reached)
        _tree, prices_json, _nodes, _wages, _goods = __import__("simulator").load()
        wage_by_trade = solve_prices.wage_ratios_by_trade(prices_json)
        rent = solve_prices.rent_hours_per_kg_by_ore_material(available, wage_by_trade)
        self.assertIn("iron_ore_kg", rent)
        self.assertGreaterEqual(rent["iron_ore_kg"], 0.0)


class WiringDoesNotBreakTheSolveTests(unittest.TestCase):
    """The whole point is a converging, honest solve - not a rent number in
    isolation. These exercise main()'s own two commanded shapes.
    """

    def test_the_ungated_solve_still_converges_with_rent_wired_in(self):
        self.assertEqual(solve_prices.main([]), 0)

    def test_the_roman_gated_solve_still_converges_with_rent_wired_in(self):
        self.assertEqual(solve_prices.main(["--civ", "rome_100ad"]), 0)

    def test_rent_never_lowers_a_price_relative_to_the_old_zero_rent_answer(self):
        # A monotonicity check on the real data: adding a nonnegative cost
        # term must never make anything cheaper. Runs the solve twice - once
        # with the rent table this file now builds, once with it forced
        # empty - and compares every resolvable material's price.
        production_entries, _duplicates = solve_prices.load_production()
        _tree, prices_json, _nodes, _wages, _goods = __import__("simulator").load()
        wage_by_trade = solve_prices.wage_ratios_by_trade(prices_json)
        producers_of = solve_prices.build_producers_index(production_entries)
        rent = solve_prices.rent_hours_per_kg_by_ore_material(
            production_entries, wage_by_trade)

        resolvable_with_rent = solve_prices.compute_resolvable_materials(
            production_entries, producers_of, rent_hours_per_kg_by_material=rent)
        prices_with_rent, _iters, _residual, _chosen = solve_prices.solve(
            production_entries, producers_of, resolvable_with_rent, wage_by_trade,
            rent_hours_per_kg_by_material=rent)

        resolvable_without_rent = solve_prices.compute_resolvable_materials(
            production_entries, producers_of)
        prices_without_rent, _iters2, _residual2, _chosen2 = solve_prices.solve(
            production_entries, producers_of, resolvable_without_rent, wage_by_trade)

        self.assertEqual(resolvable_with_rent, resolvable_without_rent)
        lowered = {material: (prices_without_rent[material], prices_with_rent[material])
                  for material in resolvable_with_rent
                  # a whisker of float slack for the damped iteration's own
                  # tolerance, not a real decrease
                  if prices_with_rent[material] < prices_without_rent[material] * (1 - 1e-6)}
        self.assertEqual(lowered, {},
                         "adding a nonnegative rent term made something CHEAPER")


if __name__ == "__main__":
    unittest.main()
