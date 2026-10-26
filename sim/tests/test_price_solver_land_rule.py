"""Land cost in the price solver's recipe costing, on synthetic entries (no data, no game)."""
import unittest

from sim.prices import solve_prices

QUICK_TOPIC = True


class LandCostIsZeroByDefaultTests(unittest.TestCase):
    """Backward compatibility: an entry with no `land_hectare_years` at all -
    every recipe in data/production/ before this task, and any future one
    that is not land-limited - must see exactly the old answer (no land
    term), not a crash and not a surprise nonzero charge.
    """

    def test_no_land_hectare_years_means_no_land_cost(self):
        entry = {"outputs": {"thing_kg": 1000.0}, "inputs": {},
                "labour_hours": {"labourer": 10.0}}
        total_cost, _prices = solve_prices.recipe_cost_and_allocation(
            "thing_kg", entry, {}, {"labourer": 1.0})
        self.assertEqual(total_cost, 10.0)

    def test_land_hectare_years_of_zero_means_no_land_cost(self):
        entry = {"outputs": {"thing_kg": 1000.0}, "inputs": {},
                "labour_hours": {"labourer": 10.0}, "land_hectare_years": 0.0}
        # Even with NO price at all for hectare_land in current_prices, a
        # stated-but-zero land_hectare_years must not return None - the
        # `if land_hectare_years:` guard in recipe_cost_and_allocation exists
        # exactly for this, mirroring rent's own "0.0 rent" convention.
        total_cost, _prices = solve_prices.recipe_cost_and_allocation(
            "thing_kg", entry, {}, {"labourer": 1.0})
        self.assertEqual(total_cost, 10.0)

    def test_an_entry_with_land_but_no_land_price_available_is_unresolvable(self):
        # A land-consuming recipe costed against a price vector that has
        # no entry for hectare_land at all must return None (the same
        # "missing input" answer an ordinary `inputs` entry gets), not
        # silently treat the missing price as zero.
        entry = {"outputs": {"crop_kg": 500.0}, "inputs": {},
                "labour_hours": {"labourer": 10.0}, "land_hectare_years": 4.0}
        result = solve_prices.recipe_cost_and_allocation(
            "crop_kg", entry, {}, {"labourer": 1.0})
        self.assertIsNone(result)


class LandCostIsAddedCorrectlyTests(unittest.TestCase):
    """The mechanism itself, on synthetic entries, independent of the real
    tables - see the module's own top docstring.
    """

    def test_land_cost_is_land_hectare_years_times_hectare_lands_price(self):
        entry = {"outputs": {"crop_kg": 500.0}, "inputs": {},
                "labour_hours": {"labourer": 10.0}, "land_hectare_years": 4.0}
        total_cost, output_prices = solve_prices.recipe_cost_and_allocation(
            "crop_kg", entry, {"hectare_land": 2.5}, {"labourer": 1.0})
        # 10 h labour + 4 hectare-yrs * 2.5 h/hectare-yr = 20 h for the batch.
        self.assertEqual(total_cost, 10.0 + 4.0 * 2.5)
        self.assertAlmostEqual(output_prices["crop_kg"], total_cost / 500.0)

    def test_land_cost_is_a_batch_level_quantity_like_labour_hours(self):
        # Doubling the batch's own outputs (same land_hectare_years, same
        # labour_hours - a bigger harvest off the SAME stated land and
        # labour) must not double the land cost; it is quoted against this
        # recipe's own `basis`, exactly like labour_hours already is.
        entry = {"outputs": {"crop_kg": 1000.0}, "inputs": {},
                "labour_hours": {"labourer": 10.0}, "land_hectare_years": 4.0}
        total_cost, _prices = solve_prices.recipe_cost_and_allocation(
            "crop_kg", entry, {"hectare_land": 2.5}, {"labourer": 1.0})
        self.assertEqual(total_cost, 10.0 + 4.0 * 2.5)

    def test_land_cost_is_independent_of_ore_rent(self):
        # A recipe can in principle carry both a land cost and its own
        # ore-style rent (not a real shape in data/production/ today, but
        # recipe_cost_and_allocation must not assume the two are mutually
        # exclusive).
        entry = {"outputs": {"odd_kg": 100.0}, "inputs": {},
                "labour_hours": {"labourer": 5.0}, "land_hectare_years": 1.0}
        total_cost, _prices = solve_prices.recipe_cost_and_allocation(
            "odd_kg", entry, {"hectare_land": 3.0}, {"labourer": 1.0},
            rent_hours_per_kg_by_material={"odd_kg": 0.1})
        # 5 h labour + 1.0 * 3.0 land + 0.1 h/kg * 100 kg rent = 18 h.
        self.assertEqual(total_cost, 5.0 + 3.0 + 10.0)


class DependencyAndAnchorTests(unittest.TestCase):
    """`_dependency_materials` and `_has_external_anchor` both have to see
    `hectare_land` as a real dependency whenever `land_hectare_years` is
    nonzero, or the resolvability/cycle-productiveness passes would treat a
    land-consuming recipe as needing nothing at all.
    """

    def test_dependency_materials_includes_hectare_land_when_stated(self):
        entry = {"inputs": {"seed_kg": 1.0}, "land_hectare_years": 4.0}
        self.assertEqual(solve_prices._dependency_materials(entry),
                        {"seed_kg", "hectare_land"})

    def test_dependency_materials_omits_hectare_land_when_absent_or_zero(self):
        self.assertEqual(solve_prices._dependency_materials({"inputs": {}}), set())
        self.assertEqual(
            solve_prices._dependency_materials({"inputs": {}, "land_hectare_years": 0.0}),
            set())

    def test_has_external_anchor_true_when_land_is_resolved(self):
        entry = {"land_hectare_years": 4.0}
        self.assertTrue(solve_prices._has_external_anchor(entry, {"hectare_land"}))

    def test_has_external_anchor_false_when_land_is_not_yet_resolved(self):
        entry = {"land_hectare_years": 4.0}
        self.assertFalse(solve_prices._has_external_anchor(entry, set()))
