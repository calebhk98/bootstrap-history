"""The price solve and its caches are keyed on everything the answer depends on: a civilisation's staple and ground, the starting
rate an off-rate solve starts from, the goods the graded energy prices are costed against. The price tables are solved on the
ground the country holds now (the land module's `home_tiles_held`), not the ground its file opened with. The solver is a recorder."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.prices import energy_prices, prices
from sim.tests import prices_stand_in

GRANTED = frozenset({"fire"})


class TerritoryFingerprint(unittest.TestCase):
    def test_a_variant_naming_another_staple_has_another_fingerprint(self):
        wheat = {"population": 1000, "home_tiles": [], "staple": "wheat_kg"}
        self.assertNotEqual(prices.territory_fingerprint(wheat), prices.territory_fingerprint(dict(wheat, staple="rice_kg")))

    def test_the_same_record_has_the_same_fingerprint(self):
        record = {"population": 1000, "home_tiles": [], "staple": "wheat_kg"}
        self.assertEqual(prices.territory_fingerprint(record), prices.territory_fingerprint(dict(record)))


class SolveKeyedOnStartingRate(unittest.TestCase):
    def solves_over(self, *records):
        stored = {"prices_in_labour_hours": {}, "resolvable_materials": [], "chosen_recipe_by_material": {},
                  "converged": True, "iterations_run": 1}
        prices.reset_caches_for_tests()
        catalogue = {}
        try:
            with mock.patch.object(prices, "_solve_to_json", return_value=stored) as solve:
                for record in records:
                    prices.solved_prices_at_wages([], {"labourer": 1.0}, catalogue, civilization=record, interest_rate=0.2)
            return solve.call_count
        finally:
            prices.reset_caches_for_tests()

    def test_two_records_differing_only_in_starting_rate_are_solved_apart_at_the_same_explicit_rate(self):
        base = {"id": "variant", "starting_interest_rate": 0.05, "home_tiles": []}
        self.assertEqual(self.solves_over(base, dict(base, starting_interest_rate=0.08)), 2)

    def test_the_same_record_is_solved_once(self):
        base = {"id": "variant", "starting_interest_rate": 0.05, "home_tiles": []}
        self.assertEqual(self.solves_over(base, dict(base)), 1)


class GradedEnergyKeyedOnGoods(unittest.TestCase):
    def test_another_goods_table_is_graded_afresh(self):
        solved = types.SimpleNamespace(gate_nodes_held=frozenset(), civilization_id="x", interest_rate=0.05,
                                       prices_in_labour_hours={}, resolvable_materials=set())
        document = {"wage_rates_denarii_per_hour": {"labourer": {"rate": 1.0}}, "money_per_labour_hour": 1.0}
        entries = {}
        with mock.patch.dict(energy_prices._CACHE, clear=True), \
                mock.patch.object(energy_prices.price_solver, "default_production_entries", return_value=entries), \
                mock.patch.object(energy_prices.price_solver, "solved_prices", return_value=solved), \
                mock.patch.object(energy_prices.price_solver, "solver_wage_ratios", return_value={}), \
                mock.patch.object(energy_prices.solve_prices_core, "techniques_available_to", return_value=({}, [], [])), \
                mock.patch.object(energy_prices, "grade_bands", return_value=({}, {}, frozenset())):
            energy_prices.graded([], document, {"thermal_mj": 1.0}, unskilled_trade="labourer")
            energy_prices.graded([], document, {"thermal_mj": 1.0}, unskilled_trade="labourer")
            self.assertEqual(len(energy_prices._CACHE), 1)
            energy_prices.graded([], document, {"thermal_mj": 2.0}, unskilled_trade="labourer")
            self.assertEqual(len(energy_prices._CACHE), 2)


class PriceTablesOnTheGroundHeldNow(unittest.TestCase):
    def tiles_given_to_the_solver(self, module):
        asked = []

        def solver(granted, document, civilization, farmed_hectares, interest_rate, unskilled_trade):
            asked.append(civilization["home_tiles"])
            return {"hectare_land": 1.0}, {"hectare_land": "derived"}

        with mock.patch.object(prices, "goods_in_hours", solver):
            module.price_tables()
        return asked

    def build(self, held):
        module = prices_stand_in.build(civilisation={"id": "test_civ", "starting_interest_rate": 0.1, "home_tiles": ["opening"]},
                                       techniques_granted=GRANTED, techniques_in_use=GRANTED, home_tiles_held=lambda: held)
        module.banded_market_rate = lambda: 0.1
        return module

    def test_the_solver_is_given_the_tiles_the_country_holds_not_the_ones_its_file_opened_with(self):
        self.assertEqual(self.tiles_given_to_the_solver(self.build(["conquered", "home"])), [["conquered", "home"]])

    def test_ground_gained_after_the_last_pricing_is_priced_again(self):
        held = ["home"]
        module = self.build(held)
        self.assertEqual(self.tiles_given_to_the_solver(module), [["home"]])
        held.append("conquered")
        self.assertEqual(self.tiles_given_to_the_solver(module), [["home", "conquered"]])


if __name__ == "__main__":
    unittest.main()
