"""Grain is milled before it is eaten as flour, so the mills' shaft work reaches the millwrights who build and
tend water wheels through household food demand (Complaint 434). Plain function calls on the loaded data."""
import json
import os
import unittest

from sim.engine.catalog import load_production_catalog
from sim.engine.solve_prices_core import techniques_available_to
from unittest import mock

from sim.labour import workforce_carriage, workforce_spinup
from sim.labour.labour_population import PopulationMixin

QUICK_TOPIC = True

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_PRODUCTION = load_production_catalog(_ROOT)


def _json(*parts):
    with open(os.path.join(_ROOT, *parts), encoding="utf-8") as handle:
        return json.load(handle)


def _shares(civ_id, extra=()):
    civ = _json("data", "civilizations", civ_id + ".json")
    reached = set(civ["starting_techs"]) | set(extra)
    return workforce_spinup.need_shares_by_trade(
        _PRODUCTION, reached, techniques_available_to, workforce_carriage.carriage_for(reached), civ)


class MillingNeedTests(unittest.TestCase):

    def test_flour_is_a_food_made_from_each_staple_grain_with_shaft_work(self):
        food_goods = _json("data", "world", "needs.json")["goods"]
        self.assertIn("food", food_goods["flour_kg"]["satisfies"])
        makers = [entry for entry in _PRODUCTION.values() if "flour_kg" in entry["outputs"]]
        self.assertGreaterEqual(len(makers), 3)
        for entry in makers:
            self.assertGreater(entry["mechanical_mj"], 0.0)
            self.assertEqual(len(entry["inputs"]), 1)

    def test_a_civilisation_with_water_power_needs_millwrights(self):
        self.assertGreater(_shares("england_1300").get("millwright", 0.0), 0.0)

    def test_a_civilisation_without_water_power_needs_none(self):
        self.assertEqual(_shares("mexica_1500").get("millwright", 0.0), 0.0)

    def test_reaching_water_power_creates_the_millwrights_demand(self):
        without = _shares("rome_100ad").get("millwright", 0.0)
        with_wheel = _shares("rome_100ad", ["cap_power_water"]).get("millwright", 0.0)
        self.assertGreater(with_wheel, without)


class DemandCoversTransportAndBuildingTests(unittest.TestCase):

    def test_rome_sailors_carters_and_plumbers_are_sized_by_need_not_the_floor(self):
        shares = _shares("rome_100ad")
        for trade in ("sailor", "carter", "plumber", "mason", "carpenter"):
            self.assertGreater(shares.get(trade, 0.0), PopulationMixin.NO_DEMAND_TRADE_SHARE, trade)

    def test_a_need_s_budget_follows_its_surplus_budget_share_not_an_equal_split(self):
        def recipe(output, trade):
            return {"outputs": {output: 1.0}, "inputs": {}, "labour_hours": {trade: 1.0},
                    "requires_node": None, "basis": "one", "yield_basis": "test", "conf": "C"}
        production = {"zz_a": recipe("zz_a", "zz_trade_a"), "zz_b": recipe("zz_b", "zz_trade_b")}
        needs = {"needs": {"zz_need_a": {"surplus_budget_share": 0.9}, "zz_need_b": {"surplus_budget_share": 0.1}},
                 "goods": {"zz_a": {"satisfies": {"zz_need_a": 1.0}}, "zz_b": {"satisfies": {"zz_need_b": 1.0}}}}
        with mock.patch.object(workforce_spinup, "_needs", return_value=needs):
            shares = workforce_spinup.need_shares_by_trade(production, set(), techniques_available_to,
                                                           workforce_carriage.Carriage())
        self.assertAlmostEqual(shares["zz_trade_a"], 0.9)
        self.assertAlmostEqual(shares["zz_trade_b"], 0.1)


if __name__ == "__main__":
    unittest.main()
