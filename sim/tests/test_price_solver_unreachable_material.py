"""Complaints/309: a material no technique in a solve can make has no price, never the solver's
starting guess. Everything the solve calls resolvable has a chosen technique."""

QUICK_TOPIC = True

import unittest

from sim.engine import solve_prices
from sim.engine import prices as price_engine
from sim.engine.solve_prices_reach import solve_priced_materials

FIRE = {"outputs": {"thermal_mj": 1.0}, "inputs": {}, "labour_hours": {"labourer": 1.0},
        "temperature_reached_c": 800.0}
HOT = {"outputs": {"hot_kg": 1.0}, "inputs": {}, "thermal_mj": 2.0, "temperature_needed_c": 1500.0,
       "labour_hours": {"labourer": 1.0}}
USES_HOT = {"outputs": {"product_kg": 1.0}, "inputs": {"hot_kg": 1.0}, "labour_hours": {"labourer": 1.0}}
PLAIN = {"outputs": {"plain_kg": 1.0}, "inputs": {}, "labour_hours": {"labourer": 1.0}}


class UnreachableMaterialTests(unittest.TestCase):

    def test_synthetic_material_no_technique_can_make_is_unpriced_with_its_dependents(self):
        entries = {"fire": FIRE, "hot": HOT, "uses_hot": USES_HOT, "plain": PLAIN}
        wages = {"labourer": 1.0}
        producers = solve_prices.build_producers_index(entries)
        resolvable = solve_prices.compute_resolvable_materials(entries, producers)
        self.assertIn("hot_kg", resolvable)    # the resolvability pass cannot see the heat floor
        prices, _iterations, _residual, chosen, resolvable = solve_priced_materials(
            entries, producers, resolvable, wages)
        self.assertEqual(resolvable, {"thermal_mj", "plain_kg"})
        self.assertEqual(set(prices), resolvable)
        self.assertEqual(set(chosen), resolvable)

    def test_every_resolvable_material_of_a_start_has_a_chosen_technique(self):
        from sim import simulator
        from sim.engine.data import load_civ
        _tree, prices_json, _nodes, _wages, _goods = simulator.load()
        entries = price_engine._default_production_entries()
        for civ_id in ("rome_100ad", "han_china_100ad"):
            civ = load_civ(civ_id)
            kwargs = {"civilization_id": civ_id, "interest_rate": float(civ["starting_interest_rate"])}
            held = frozenset(civ["starting_techs"])
            solved = price_engine.solved_prices(held, prices_json, **kwargs)
            in_reach = price_engine.solved_prices(
                solved.gate_nodes_held, prices_json, admitted_entry_keys=price_engine.entries_in_reach(
                    held, solved.gate_nodes_held, solved.resolvable_materials, entries), **kwargs)
            for name, table in (("solved", solved), ("in reach", in_reach)):
                guessed = sorted(table.resolvable_materials - set(table.chosen_recipe_by_material))
                self.assertEqual(guessed, [], "%s %s table prices from the starting guess" % (civ_id, name))
                self.assertEqual(set(table.prices_in_labour_hours), table.resolvable_materials)


if __name__ == "__main__":
    unittest.main()
