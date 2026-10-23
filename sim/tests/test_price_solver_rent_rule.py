"""Rent in the price solver's recipe costing, on synthetic entries (no data, no game)."""
import unittest

from sim.engine import solve_prices

QUICK_TOPIC = True


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
