"""Land rent is per civilisation (RENT NEEDS A CIVILIZATION in sim/prices/prices.py). `solved_prices_at_wages` keys its cache on
the civilisation as well as the gate nodes held, so two civilisations holding the same gate nodes never share a land price,
and an unset civilisation is the default one; `_solve_to_json` charges the opening's stand-in rent for that civilisation unless
the caller names a rent. The solver and the rent stand-in are recorders; no price solve. The rent rule itself is in
test_price_solver_land."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.prices import prices

DEFAULT_CIVILISATION = "default_civ"
STORED = {"prices_in_labour_hours": {"hectare_land": 1.0}, "resolvable_materials": ["hectare_land"],
          "chosen_recipe_by_material": {}, "converged": True, "iterations_run": 3}
ENTRIES = {"entry": {}}


class SolveCacheKeyTests(unittest.TestCase):
    def solve(self, *civilization_ids, held=("gate",)):
        """The results of solving once per id on one cache, and the civilisation ids the solver was run for."""
        asked = []

        def solved(entries, gates, civilization_id, *rest):
            asked.append(civilization_id)
            return dict(STORED)

        standin = types.SimpleNamespace(DEFAULT_LAND_CIVILIZATION=DEFAULT_CIVILISATION,
                                        load_starting_interest_rate=lambda civilization_id: 0.1)
        with mock.patch.object(prices, "_SOLVE_CACHE", {}), mock.patch.object(prices, "solve_prices", standin), \
                mock.patch.object(prices, "all_gate_nodes", return_value=frozenset({"gate"})), \
                mock.patch.object(prices, "_solve_to_json", side_effect=solved):
            results = [prices.solved_prices_at_wages(held, {"smith": 2.0}, ENTRIES, civilization_id=civilization_id)
                       for civilization_id in civilization_ids]
        return results, asked

    def test_the_same_gate_nodes_for_another_civilisation_is_a_cache_miss(self):
        (rome, han), asked = self.solve("rome", "han")
        self.assertIsNot(rome, han)
        self.assertEqual(asked, ["rome", "han"])

    def test_the_same_gate_nodes_for_the_same_civilisation_is_a_cache_hit(self):
        (first, second), asked = self.solve("rome", "rome")
        self.assertIs(first, second)
        self.assertEqual(asked, ["rome"])

    def test_an_unset_civilisation_is_the_default_one_and_hits_its_cache_entry(self):
        (unset, named), asked = self.solve(None, DEFAULT_CIVILISATION)
        self.assertIs(unset, named)
        self.assertEqual(asked, [DEFAULT_CIVILISATION])

    def test_the_result_records_which_civilisation_it_was_solved_for(self):
        (result,), _asked = self.solve("mexica")
        self.assertEqual(result.civilization_id, "mexica")


class SolveToJsonRentTests(unittest.TestCase):
    def run_solve(self, rent=None, civilization_id="rome"):
        stand_in = mock.Mock(return_value={"hectare_land": 12.0})
        solver = mock.Mock(return_value=({"hectare_land": 1.0}, 3, 0.0, {}, set()))
        solve_prices = types.SimpleNamespace(
            techniques_available_to=lambda entries, gates: ({"entry": {}}, [], []),
            build_producers_index=lambda entries: {}, compute_resolvable_materials=mock.Mock(return_value=set()),
            CONVERGENCE_TOLERANCE=1e-9)
        with mock.patch.object(prices, "solve_prices", solve_prices), \
                mock.patch.object(prices, "rent_standin", types.SimpleNamespace(stand_in_rent=stand_in)), \
                mock.patch.object(prices, "solve_prices_reach", types.SimpleNamespace(solve_priced_materials=solver)), \
                mock.patch.object(prices, "solver_wage_ratios", return_value={"smith": 2.0}):
            prices._solve_to_json(ENTRIES, frozenset(), civilization_id, {"smith": 2.0},
                                  rent_hours_per_kg_by_material=rent)
        return stand_in, solver, solve_prices.compute_resolvable_materials

    def test_with_no_rent_named_the_standin_for_that_civilisation_is_charged(self):
        stand_in, solver, resolvable = self.run_solve()
        self.assertEqual(stand_in.call_args.kwargs["civilization_id"], "rome")
        self.assertEqual(solver.call_args.kwargs["rent_hours_per_kg_by_material"], {"hectare_land": 12.0})
        self.assertEqual(resolvable.call_args.kwargs["rent_hours_per_kg_by_material"], {"hectare_land": 12.0})

    def test_a_rent_the_caller_names_replaces_the_standin(self):
        stand_in, solver, _resolvable = self.run_solve(rent={"hectare_land": 3.0})
        stand_in.assert_not_called()
        self.assertEqual(solver.call_args.kwargs["rent_hours_per_kg_by_material"], {"hectare_land": 3.0})

    def test_an_empty_rent_charges_none_at_all(self):
        stand_in, solver, _resolvable = self.run_solve(rent={})
        stand_in.assert_not_called()
        self.assertEqual(solver.call_args.kwargs["rent_hours_per_kg_by_material"], {})


if __name__ == "__main__":
    unittest.main()
