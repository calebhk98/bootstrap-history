"""Land rent is per civilisation (RENT NEEDS A CIVILIZATION in sim/prices/prices.py). `solved_prices_at_wages` keys its cache on
the civilisation as well as the gate nodes held, so two civilisations holding the same gate nodes never share a land price,
and an unset civilisation is the record of the default one; `_solve_to_json` charges the opening's stand-in rent for that
civilisation record unless the caller names a rent. The solver and the rent stand-in are recorders; no price solve. The rent
rule itself is in test_price_solver_land."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.prices import prices, solve_prices_core

STORED = {"prices_in_labour_hours": {"hectare_land": 1.0}, "resolvable_materials": ["hectare_land"],
          "chosen_recipe_by_material": {}, "converged": True, "iterations_run": 3}
ENTRIES = {"entry": {}}


def record(civilization_id):
    return {"id": civilization_id, "starting_interest_rate": 0.1, "home_regions": []}


class SolveCacheKeyTests(unittest.TestCase):
    def solve(self, *civilizations, held=("gate",)):
        """The results of solving once per record on one cache, and the civilisation ids the solver was run for."""
        asked = []

        def solved(entries, gates, document_ratios, civilization, *rest):
            asked.append(civilization["id"])
            return dict(STORED)

        with mock.patch.object(prices, "_SOLVE_CACHE", {}), \
                mock.patch.object(prices, "all_gate_nodes", return_value=frozenset({"gate"})), \
                mock.patch.object(prices, "_solve_to_json", side_effect=solved):
            results = [prices.solved_prices_at_wages(held, {"smith": 2.0}, ENTRIES, civilization=civilization)
                       for civilization in civilizations]
        return results, asked

    def test_the_same_gate_nodes_for_another_civilisation_is_a_cache_miss(self):
        (rome, han), asked = self.solve(record("rome"), record("han"))
        self.assertIsNot(rome, han)
        self.assertEqual(asked, ["rome", "han"])

    def test_the_same_gate_nodes_for_the_same_civilisation_is_a_cache_hit(self):
        (first, second), asked = self.solve(record("rome"), record("rome"))
        self.assertIs(first, second)
        self.assertEqual(asked, ["rome"])

    def test_the_result_records_which_civilisation_it_was_solved_for(self):
        (result,), _asked = self.solve(record("mexica"))
        self.assertEqual(result.civilization_id, "mexica")


class CivilizationRecordTests(unittest.TestCase):
    def test_a_record_the_caller_holds_is_the_record(self):
        held = record("held")
        self.assertIs(prices.civilization_record(held, "another_id"), held)

    def test_no_record_and_no_id_is_the_default_civilisations_record(self):
        default = types.SimpleNamespace(record=record("default_civ"))
        with mock.patch("sim.prices.engine_seam.load_civ", return_value=default.record) as loaded:
            self.assertIs(prices.civilization_record(None), default.record)
        loaded.assert_called_once_with(None)

    def test_an_id_that_names_no_record_is_an_error_not_an_empty_territory(self):
        with mock.patch("sim.prices.engine_seam.load_civ", side_effect=SystemExit("unknown civilization")):
            with self.assertRaises(SystemExit):
                prices.civilization_record(None, "atlantis")


class SolveToJsonRentTests(unittest.TestCase):
    def run_solve(self, rent=None, civilization_id="rome"):
        stand_in = mock.Mock(return_value={"hectare_land": 12.0})
        solver = mock.Mock(return_value=({"hectare_land": 1.0}, 3, 0.0, {}, set()))
        resolvable = mock.Mock(return_value=set())
        civilization = record(civilization_id)
        with mock.patch.object(solve_prices_core, "techniques_available_to", lambda entries, gates: ({"entry": {}}, [], [])), \
                mock.patch.object(solve_prices_core, "build_producers_index", lambda entries: {}), \
                mock.patch.object(solve_prices_core, "compute_resolvable_materials", resolvable), \
                mock.patch.object(prices, "rent_standin", types.SimpleNamespace(stand_in_rent=stand_in)), \
                mock.patch.object(prices, "solve_prices_reach", types.SimpleNamespace(solve_priced_materials=solver)), \
                mock.patch.object(prices, "solver_wage_ratios", return_value={"smith": 2.0}):
            prices._solve_to_json(ENTRIES, frozenset(), {"smith": 2.0}, civilization,
                                  rent_hours_per_kg_by_material=rent)
        return stand_in, solver, resolvable, civilization

    def test_with_no_rent_named_the_standin_for_that_civilisation_is_charged(self):
        stand_in, solver, resolvable, civilization = self.run_solve()
        self.assertIs(stand_in.call_args.args[2], civilization)
        self.assertEqual(solver.call_args.kwargs["rent_hours_per_kg_by_material"], {"hectare_land": 12.0})
        self.assertEqual(resolvable.call_args.kwargs["rent_hours_per_kg_by_material"], {"hectare_land": 12.0})

    def test_a_rent_the_caller_names_replaces_the_standin(self):
        stand_in, solver, _resolvable, _civilization = self.run_solve(rent={"hectare_land": 3.0})
        stand_in.assert_not_called()
        self.assertEqual(solver.call_args.kwargs["rent_hours_per_kg_by_material"], {"hectare_land": 3.0})

    def test_an_empty_rent_charges_none_at_all(self):
        stand_in, solver, _resolvable, _civilization = self.run_solve(rent={})
        stand_in.assert_not_called()
        self.assertEqual(solver.call_args.kwargs["rent_hours_per_kg_by_material"], {})


if __name__ == "__main__":
    unittest.main()
