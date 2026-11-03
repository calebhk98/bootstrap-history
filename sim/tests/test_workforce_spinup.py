"""The need each trade carries comes from household demand through the recipe graph, not from
authored shares; the yearly split of hours is plain arithmetic on the numbers handed in (Complaint 640: the
the opening's determinism is held by test_deterministic_for_a_given_input)."""
QUICK_TOPIC = True

import copy
import glob
import json
import os
import unittest

from sim.labour import trade_data
from sim.content.catalog import load_production_catalog
from sim.prices.solve_prices_core import techniques_available_to
from sim.labour import workforce_carriage, workforce_spinup
from sim.world import need_demand

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CIV_PATHS = sorted(glob.glob(os.path.join(_ROOT, "data", "civilizations", "*.json")))
_PRODUCTION = load_production_catalog(_ROOT)


def _civilisations():
    for path in _CIV_PATHS:
        with open(path, encoding="utf-8") as handle:
            civ = json.load(handle)
        if civ.get("id"):
            yield civ


def _trades_of_recipe(entry):
    trades = set(entry.get("labour_hours") or {})
    for capital in entry.get("capital") or ():
        trades.update(capital.get("build_labour_hours") or {})
    return trades


def _trades_of_available_recipes(production, reached):
    available, _unreached, _unclassified = techniques_available_to(production, reached)
    trades = set()
    for entry in available.values():
        trades.update(_trades_of_recipe(entry))
    return trades


def _shares(production, reached, civ=None):
    return workforce_spinup.need_shares_by_trade(
        production, set(reached), techniques_available_to,
        workforce_carriage.carriage_for(reached), civ)


class NeedSharesTests(unittest.TestCase):

    def test_the_shares_of_every_base_civilisation_add_up_to_one(self):
        for civ in _civilisations():
            self.assertAlmostEqual(sum(_shares(_PRODUCTION, civ["starting_techs"]).values()), 1.0, places=9)

    def test_a_trade_with_an_available_recipe_goes_without_a_share_only_for_goods_no_need_names(self):
        # A trade whose every recipe makes a good no need names has no demand of its own unless a recipe
        # uses the good (shaft work in a start that holds water power but runs nothing that draws it); the labour
        # package floors such trades (NO_DEMAND_TRADE_SHARE). Any other trade must be in the shares.
        farm_trade = trade_data.farm_trade()
        needs = need_demand.load_needs(_ROOT)
        for civ in _civilisations():
            reached = set(civ["starting_techs"])
            shares = _shares(_PRODUCTION, reached, civ)
            available, _unreached, _unclassified = techniques_available_to(_PRODUCTION, reached)
            carriers = workforce_carriage.carriage_for(reached).trades()
            expected = (_trades_of_available_recipes(_PRODUCTION, reached) | carriers) - {farm_trade}
            self.assertLessEqual({trade for trade, share in shares.items() if share > 0.0}, expected, civ["id"])
            named = {good for good, attributes in need_demand.goods_attributes(needs, available).items()
                     if attributes["satisfies"]}
            for trade in expected - set(shares):
                for recipe_id, entry in available.items():
                    if trade in _trades_of_recipe(entry):
                        self.assertNotIn(workforce_spinup._dominant_output(entry), named, (civ["id"], trade, recipe_id))
            self.assertTrue(all(share >= 0.0 for share in shares.values()))

    def test_every_base_civilisation_splits_its_non_farm_need_across_more_than_one_trade(self):
        for civ in _civilisations():
            shares = _shares(_PRODUCTION, civ["starting_techs"], civ)
            self.assertGreater(len([share for share in shares.values() if share > 0.0]), 1, civ["id"])

    def test_civilisations_with_different_technology_split_differently(self):
        splits = [_shares(_PRODUCTION, civ["starting_techs"]) for civ in _civilisations()]
        self.assertGreater(len({tuple(sorted(split)) for split in splits}), 1)

    def test_a_mod_trade_with_an_available_recipe_gets_a_share(self):
        production = copy.deepcopy(_PRODUCTION)
        production["zz_gadget"] = {
            "outputs": {"zz_gadget": 1.0}, "inputs": {"iron_bar_kg": 0.5}, "satisfies": {"shelter": 1.0},
            "labour_hours": {"zz_wright": 3.0}, "requires_node": None,
            "basis": "one gadget", "yield_basis": "test", "conf": "C"}
        production["zz_locked"] = {
            "outputs": {"zz_locked": 1.0}, "inputs": {},
            "labour_hours": {"zz_sage": 3.0}, "requires_node": "zz_unreached_node",
            "basis": "one locked", "yield_basis": "test", "conf": "C"}
        civ = next(_civilisations())
        shares = _shares(production, civ["starting_techs"])
        self.assertGreater(shares.get("zz_wright", 0.0), 0.0)
        self.assertEqual(shares.get("zz_sage", 0.0), 0.0)
        # The wright also draws iron, so the smith side of the graph is busier.
        self.assertNotEqual(_shares(_PRODUCTION, civ["starting_techs"]), shares)

    def test_deterministic_for_a_given_input(self):
        civ = next(_civilisations())
        self.assertEqual(_shares(_PRODUCTION, civ["starting_techs"]), _shares(_PRODUCTION, civ["starting_techs"]))


if __name__ == "__main__":
    unittest.main()
