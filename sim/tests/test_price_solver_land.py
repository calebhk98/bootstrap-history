"""Pins the fix for Complaints/49 ("land rent reaches no crop"): two rounds of
work built a real, per-civilization Ricardian rent on `iugerum_land` in
`sim/world/land.py`, and `sim/solve_prices.py` already turned that into
`iugerum_land`'s own solved price - but nothing in `data/production/` ever
consumed `iugerum_land`. `wheat_kg` had `inputs={}`, and so did every other
material whose own prose said it came "from arable land", "from pasture" or
"from forest". The rent was computed and then discarded; no loaf of bread was
ever dearer for it. `land_iugera_years` (see LAND in
`data/production/_SCHEMA.md`) and the corresponding `land_cost_hours` term in
`recipe_cost_and_allocation` are the fix.

Written as unittest.TestCase against solve_prices directly, like
test_price_solver_rent.py and test_price_solver_era_gate.py, so it does not
drag in the engine. A few tests use the real data/production/ and
data/world/geography.json tables (an integration check that the real land
mechanism and the real crop entries actually wire together and stay
convergent, and that the five civilizations' differing rents actually
separate their crop prices); the rest build tiny synthetic entries so the
mechanism itself is pinned independent of any future edit to those data
files.
"""
import unittest

from sim import solve_prices


class LandCostIsZeroByDefaultTests(unittest.TestCase):
    """Backward compatibility: an entry with no `land_iugera_years` at all -
    every recipe in data/production/ before this task, and any future one
    that is not land-limited - must see exactly the old answer (no land
    term), not a crash and not a surprise nonzero charge.
    """

    def test_no_land_iugera_years_means_no_land_cost(self):
        entry = {"outputs": {"thing_kg": 1000.0}, "inputs": {},
                "labour_hours": {"labourer": 10.0}}
        total_cost, _prices = solve_prices.recipe_cost_and_allocation(
            "thing_kg", entry, {}, {"labourer": 1.0})
        self.assertEqual(total_cost, 10.0)

    def test_land_iugera_years_of_zero_means_no_land_cost(self):
        entry = {"outputs": {"thing_kg": 1000.0}, "inputs": {},
                "labour_hours": {"labourer": 10.0}, "land_iugera_years": 0.0}
        # Even with NO price at all for iugerum_land in current_prices, a
        # stated-but-zero land_iugera_years must not return None - the
        # `if land_iugera_years:` guard in recipe_cost_and_allocation exists
        # exactly for this, mirroring rent's own "0.0 rent" convention.
        total_cost, _prices = solve_prices.recipe_cost_and_allocation(
            "thing_kg", entry, {}, {"labourer": 1.0})
        self.assertEqual(total_cost, 10.0)

    def test_an_entry_with_land_but_no_land_price_available_is_unresolvable(self):
        # A land-consuming recipe costed against a price vector that has
        # no entry for iugerum_land at all must return None (the same
        # "missing input" answer an ordinary `inputs` entry gets), not
        # silently treat the missing price as zero.
        entry = {"outputs": {"crop_kg": 500.0}, "inputs": {},
                "labour_hours": {"labourer": 10.0}, "land_iugera_years": 4.0}
        result = solve_prices.recipe_cost_and_allocation(
            "crop_kg", entry, {}, {"labourer": 1.0})
        self.assertIsNone(result)


class LandCostIsAddedCorrectlyTests(unittest.TestCase):
    """The mechanism itself, on synthetic entries, independent of the real
    tables - see the module's own top docstring.
    """

    def test_land_cost_is_land_iugera_years_times_iugerum_lands_price(self):
        entry = {"outputs": {"crop_kg": 500.0}, "inputs": {},
                "labour_hours": {"labourer": 10.0}, "land_iugera_years": 4.0}
        total_cost, output_prices = solve_prices.recipe_cost_and_allocation(
            "crop_kg", entry, {"iugerum_land": 2.5}, {"labourer": 1.0})
        # 10 h labour + 4 iugera-yrs * 2.5 h/iugerum-yr = 20 h for the batch.
        self.assertEqual(total_cost, 10.0 + 4.0 * 2.5)
        self.assertAlmostEqual(output_prices["crop_kg"], total_cost / 500.0)

    def test_land_cost_is_a_batch_level_quantity_like_labour_hours(self):
        # Doubling the batch's own outputs (same land_iugera_years, same
        # labour_hours - a bigger harvest off the SAME stated land and
        # labour) must not double the land cost; it is quoted against this
        # recipe's own `basis`, exactly like labour_hours already is.
        entry = {"outputs": {"crop_kg": 1000.0}, "inputs": {},
                "labour_hours": {"labourer": 10.0}, "land_iugera_years": 4.0}
        total_cost, _prices = solve_prices.recipe_cost_and_allocation(
            "crop_kg", entry, {"iugerum_land": 2.5}, {"labourer": 1.0})
        self.assertEqual(total_cost, 10.0 + 4.0 * 2.5)

    def test_land_cost_is_independent_of_ore_rent(self):
        # A recipe can in principle carry both a land cost and its own
        # ore-style rent (not a real shape in data/production/ today, but
        # recipe_cost_and_allocation must not assume the two are mutually
        # exclusive).
        entry = {"outputs": {"odd_kg": 100.0}, "inputs": {},
                "labour_hours": {"labourer": 5.0}, "land_iugera_years": 1.0}
        total_cost, _prices = solve_prices.recipe_cost_and_allocation(
            "odd_kg", entry, {"iugerum_land": 3.0}, {"labourer": 1.0},
            rent_hours_per_kg_by_material={"odd_kg": 0.1})
        # 5 h labour + 1.0 * 3.0 land + 0.1 h/kg * 100 kg rent = 18 h.
        self.assertEqual(total_cost, 5.0 + 3.0 + 10.0)


class DependencyAndAnchorTests(unittest.TestCase):
    """`_dependency_materials` and `_has_external_anchor` both have to see
    `iugerum_land` as a real dependency whenever `land_iugera_years` is
    nonzero, or the resolvability/cycle-productiveness passes would treat a
    land-consuming recipe as needing nothing at all.
    """

    def test_dependency_materials_includes_iugerum_land_when_stated(self):
        entry = {"inputs": {"seed_kg": 1.0}, "land_iugera_years": 4.0}
        self.assertEqual(solve_prices._dependency_materials(entry),
                        {"seed_kg", "iugerum_land"})

    def test_dependency_materials_omits_iugerum_land_when_absent_or_zero(self):
        self.assertEqual(solve_prices._dependency_materials({"inputs": {}}), set())
        self.assertEqual(
            solve_prices._dependency_materials({"inputs": {}, "land_iugera_years": 0.0}),
            set())

    def test_has_external_anchor_true_when_land_is_resolved(self):
        entry = {"land_iugera_years": 4.0}
        self.assertTrue(solve_prices._has_external_anchor(entry, {"iugerum_land"}))

    def test_has_external_anchor_false_when_land_is_not_yet_resolved(self):
        entry = {"land_iugera_years": 4.0}
        self.assertFalse(solve_prices._has_external_anchor(entry, set()))


class LandRentReferencePriceStaysZeroRentTests(unittest.TestCase):
    """`land_rent_hours_per_iugerum` converts sim/world/land.py's physical
    rent into hours using wheat_kg's own ZERO-LAND-RENT reference price -
    this must stay true now that wheat_kg itself states a
    `land_iugera_years`, or the whole mechanism would be circular (land's
    price depending on a wheat price that itself depends on land's price).
    """

    def test_reference_price_ignores_wheats_own_land_iugera_years(self):
        # A synthetic wheat_kg with a land_iugera_years large enough that,
        # if it were NOT zeroed out for this one reference calculation,
        # would swamp the labour-only answer.
        wheat_entry = {"outputs": {"wheat_kg": 500.0}, "inputs": {},
                       "labour_hours": {"labourer": 100.0},
                       "land_iugera_years": 1000.0}
        entries = {"wheat_kg": wheat_entry}
        rent = solve_prices.land_rent_hours_per_iugerum(
            entries, {"labourer": 1.0}, civilization_id="rome_100ad")
        # This only asserts the function runs and returns SOMETHING (real
        # sim/world/land.py data behind civilization_id="rome_100ad") -
        # the real guard is the next test, which checks the VALUE does not
        # move when land_iugera_years changes.
        self.assertIsInstance(rent, dict)

    def test_reference_price_is_unaffected_by_the_size_of_land_iugera_years(self):
        wage_by_trade = {"labourer": 1.0}
        small = solve_prices.land_rent_hours_per_iugerum(
            {"wheat_kg": {"outputs": {"wheat_kg": 500.0}, "inputs": {},
                         "labour_hours": {"labourer": 100.0},
                         "land_iugera_years": 1.0}},
            wage_by_trade, civilization_id="rome_100ad")
        large = solve_prices.land_rent_hours_per_iugerum(
            {"wheat_kg": {"outputs": {"wheat_kg": 500.0}, "inputs": {},
                         "labour_hours": {"labourer": 100.0},
                         "land_iugera_years": 1e6}},
            wage_by_trade, civilization_id="rome_100ad")
        self.assertEqual(small, large)

    def test_the_real_wheat_entry_still_produces_a_positive_rome_rent(self):
        # Integration check against the committed data/production/ and
        # sim/world/land.py - no pinned number (both are owned elsewhere
        # and can change), only the structural property that Rome's own
        # multi-region territory still earns a positive rent now that
        # wheat_kg itself consumes iugerum_land.
        production_entries, duplicates = solve_prices.load_production()
        self.assertEqual(duplicates, [])
        self.assertIn("land_iugera_years", production_entries["wheat_kg"])
        wage_by_trade = {"labourer": 1.0}
        rent = solve_prices.land_rent_hours_per_iugerum(
            production_entries, wage_by_trade, civilization_id="rome_100ad")
        self.assertIn("iugerum_land", rent)
        self.assertGreater(rent["iugerum_land"], 0.0)


class TheFiveCivilizationsSeparateTests(unittest.TestCase):
    """The headline claim Complaints/49 asks for: land-scarce civilizations
    must now pay MORE for a land-limited crop than land-abundant ones, not
    the same book-identical price every civilization paid before this task
    (wheat_kg's price used to be pure labour, so it was IDENTICAL across
    every civilization regardless of how much land any of them held).
    """

    CIVILIZATIONS_BY_EXPECTED_RENT_ORDER = (
        # Descending order of land rent, per this task's own measurement -
        # not pinned as an exact number (sim/world/land.py is owned
        # elsewhere and its inputs can change), only as an ORDERING, and
        # only used to state the monotonicity this test actually checks.
        "rome_100ad", "han_china_100ad", "mexica_1500", "england_1300",
        "norse_900ad",
    )

    def _solved_wheat_price(self, civilization_id):
        production_entries, _duplicates = solve_prices.load_production()
        reached = solve_prices.load_starting_technologies(civilization_id)
        available, _unreached, _unclassified = solve_prices.techniques_available_to(
            production_entries, reached)
        _tree, prices_json, _nodes, _w, _g = __import__("simulator").load()
        wage_by_trade = solve_prices.wage_ratios_by_trade(prices_json)
        producers_of = solve_prices.build_producers_index(available)
        rent = solve_prices.rent_hours_per_kg_by_ore_material(available, wage_by_trade)
        rent.update(solve_prices.land_rent_hours_per_iugerum(
            available, wage_by_trade, civilization_id=civilization_id))
        resolvable = solve_prices.compute_resolvable_materials(
            available, producers_of, rent_hours_per_kg_by_material=rent)
        prices, _iters, _residual, _chosen = solve_prices.solve(
            available, producers_of, resolvable, wage_by_trade,
            rent_hours_per_kg_by_material=rent)
        return prices["wheat_kg"], rent.get("iugerum_land", 0.0)

    def test_wheat_price_is_no_longer_identical_across_civilizations(self):
        prices = {civ: self._solved_wheat_price(civ)[0]
                 for civ in self.CIVILIZATIONS_BY_EXPECTED_RENT_ORDER}
        self.assertGreater(len(set(prices.values())), 1,
                           "every civilization still pays the same wheat "
                           "price - land rent is not reaching the crop")

    def test_wheat_price_ranks_with_land_rent_not_against_it(self):
        # A civilization that pays MORE rent per iugerum must pay AT LEAST
        # as much for wheat as one that pays less - the whole point of
        # wiring land into the crop's cost. Uses each civilization's OWN
        # solved rent (not a pinned number) so this stays true even if
        # sim/world/land.py's own inputs change later.
        measurements = [self._solved_wheat_price(civ)
                        for civ in self.CIVILIZATIONS_BY_EXPECTED_RENT_ORDER]
        by_rent = sorted(measurements, key=lambda pair: pair[1])
        wheat_prices_by_ascending_rent = [price for price, _rent in by_rent]
        self.assertEqual(wheat_prices_by_ascending_rent,
                         sorted(wheat_prices_by_ascending_rent),
                         "wheat's solved price does not rise with land rent")


class WhichMaterialsCarryLandTests(unittest.TestCase):
    """Pins the considered list in data/production/_SCHEMA.md's own LAND
    section: every material given `land_iugera_years`, and a sample of the
    ones deliberately left without it, with the reasons this task recorded.
    """

    @classmethod
    def setUpClass(cls):
        cls.production_entries, _duplicates = solve_prices.load_production()

    def test_the_primary_grown_and_land_limited_materials_all_carry_it(self):
        expected = {
            "wheat_kg", "olive_oil_kg", "wine_common_kg", "cotton_kg",
            "hemp_fiber_kg", "linen_kg", "silk_kg", "rose_petals_kg",
            "dye_kg", "wool_kg", "milk_kg", "timber_m3", "wood_kg",
            "firewood_kg", "cork_kg", "oak_bark_kg", "shellac_kg",
            "rubber_kg", "ox", "mule",
        }
        for material in expected:
            entry = self.production_entries.get(material)
            self.assertIsNotNone(entry, material)
            self.assertTrue(entry.get("land_iugera_years"),
                            "%s should carry a positive land_iugera_years" % material)

    def test_livestock_byproducts_and_the_two_not_land_limited_entries_do_not(self):
        # hide_kg and kin: their own yield_basis declines to charge the
        # animal's land/feed cost, to avoid double-counting once a meat
        # entry exists. beeswax_kg and papyrus_sheet: their own yield_basis
        # states directly that land is not their binding constraint.
        excluded = {"hide_kg", "bone_kg", "bristles_kg", "horsehair_kg",
                   "fat_kg", "manure_kg", "beeswax_kg", "papyrus_sheet"}
        for material in excluded:
            entry = self.production_entries.get(material)
            self.assertIsNotNone(entry, material)
            self.assertFalse(entry.get("land_iugera_years"),
                            "%s should not carry land_iugera_years" % material)


class WiringDoesNotBreakTheSolveTests(unittest.TestCase):
    """The whole point is a converging, honest solve - not a price number in
    isolation. These exercise main()'s own two commanded shapes, the same
    way test_price_solver_rent.py's own analogous class does.
    """

    def test_the_ungated_solve_still_converges_with_land_wired_in(self):
        self.assertEqual(solve_prices.main([]), 0)

    def test_the_roman_gated_solve_still_converges_with_land_wired_in(self):
        self.assertEqual(solve_prices.main(["--civ", "rome_100ad"]), 0)

    def test_land_never_lowers_a_price_relative_to_the_old_zero_land_answer(self):
        # A monotonicity check on the real data: adding a nonnegative land
        # cost term must never make anything cheaper. Runs the solve twice
        # - once with land wired in, once with every land_iugera_years
        # stripped out - and compares every resolvable material's price.
        #
        # EXCEPT for minor joint byproducts with no independent price
        # anchor (see JOINT BYPRODUCTS WITHOUT AN INDEPENDENT ANCHOR in the
        # module docstring and `minor_joint_byproducts_are_unanchored`) -
        # germanium_g and indium_g today, both mass-split artifacts of
        # zinc_electrolytic_kg's own value-share allocation rather than
        # independently derived prices. Their number is free to move,
        # including downward, when the REST of the economy shifts around
        # them even though their own recipe is untouched - that is what
        # "not a derived number" means, not a bug this task introduced.
        # Checked in BOTH directions (with-land and without-land) so a
        # material is excluded only when the mechanism itself says its
        # price carries no independent meaning, never merely because it
        # happens to have moved.
        production_entries, _duplicates = solve_prices.load_production()
        stripped_entries = {
            recipe_id: {key: value for key, value in entry.items()
                       if key != "land_iugera_years"}
            for recipe_id, entry in production_entries.items()}
        _tree, prices_json, _nodes, _w, _g = __import__("simulator").load()
        wage_by_trade = solve_prices.wage_ratios_by_trade(prices_json)

        producers_of = solve_prices.build_producers_index(production_entries)
        rent = solve_prices.rent_hours_per_kg_by_ore_material(
            production_entries, wage_by_trade)
        rent.update(solve_prices.land_rent_hours_per_iugerum(
            production_entries, wage_by_trade))
        resolvable_with_land = solve_prices.compute_resolvable_materials(
            production_entries, producers_of, rent_hours_per_kg_by_material=rent)
        prices_with_land, _iters, _residual, chosen_with_land = solve_prices.solve(
            production_entries, producers_of, resolvable_with_land, wage_by_trade,
            rent_hours_per_kg_by_material=rent)
        unanchored_with_land = solve_prices.minor_joint_byproducts_are_unanchored(
            production_entries, chosen_with_land, prices_with_land, wage_by_trade,
            rent_hours_per_kg_by_material=rent)

        producers_of_stripped = solve_prices.build_producers_index(stripped_entries)
        rent_stripped = solve_prices.rent_hours_per_kg_by_ore_material(
            stripped_entries, wage_by_trade)
        rent_stripped.update(solve_prices.land_rent_hours_per_iugerum(
            stripped_entries, wage_by_trade))
        resolvable_without_land = solve_prices.compute_resolvable_materials(
            stripped_entries, producers_of_stripped,
            rent_hours_per_kg_by_material=rent_stripped)
        prices_without_land, _iters2, _residual2, chosen_without_land = solve_prices.solve(
            stripped_entries, producers_of_stripped, resolvable_without_land,
            wage_by_trade, rent_hours_per_kg_by_material=rent_stripped)
        unanchored_without_land = solve_prices.minor_joint_byproducts_are_unanchored(
            stripped_entries, chosen_without_land, prices_without_land, wage_by_trade,
            rent_hours_per_kg_by_material=rent_stripped)

        unanchored = set(unanchored_with_land) | set(unanchored_without_land)
        common = (resolvable_with_land & resolvable_without_land) - unanchored
        lowered = {material: (prices_without_land[material], prices_with_land[material])
                  for material in common
                  # a whisker of float slack for the damped iteration's own
                  # tolerance, not a real decrease
                  if prices_with_land[material] < prices_without_land[material] * (1 - 1e-6)}
        self.assertEqual(lowered, {},
                         "adding a nonnegative land cost term made something CHEAPER")


if __name__ == "__main__":
    unittest.main()
