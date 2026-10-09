"""The need each trade carries comes from household demand through the recipe graph, not from
authored shares; the engine's starting hours by trade follow it or the labour core's people."""
import copy
import glob
import json
import os
import unittest

from .harness import *  # noqa: F401,F403
from sim.labour import labour_allocation
from sim.engine.catalog import load_production_catalog
from sim.engine.solve_prices_core import techniques_available_to
from sim.world import agriculture
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
        farm_trade = labour_allocation.FARM_TRADE
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

    def test_the_same_seed_gives_the_same_starting_workforce(self):
        first = sim(civ="rome_100ad", events=False)
        second = sim(civ="rome_100ad", events=False)
        for test_sim in (first, second):
            test_sim._demographic_recovery(101)
        self.assertEqual(first.state.economy.society_labour_hours,
                         second.state.economy.society_labour_hours)


class EngineStartTests(unittest.TestCase):

    def _first_year(self, civ_id):
        test_sim = sim(civ=civ_id, events=False)
        test_sim._demographic_recovery(test_sim.civ.get("year", 100) + 1)
        return test_sim, test_sim.state.economy.society_labour_hours

    def test_start_workforce_is_split_by_trade_not_pooled(self):
        for civ in _civilisations():
            _test_sim, hours = self._first_year(civ["id"])
            expected = (_trades_of_available_recipes(_PRODUCTION, set(civ["starting_techs"]))
                        | workforce_carriage.carriage_for(civ["starting_techs"]).trades()
                        | {labour_allocation.FARM_TRADE})
            held = {trade for trade, value in hours.items() if value > 0.0}
            # a trade the labour core holds nobody in (none needed it at the opening) has no hours
            self.assertLessEqual(held, expected, civ["id"])
            self.assertGreater(len(held), 1, civ["id"])

    def test_farm_share_matches_the_farm_labour_logic(self):
        for civ in _civilisations():
            test_sim = sim(civ=civ["id"], events=False)
            adult_equivalent = test_sim._adult_equivalent_population(test_sim.population)
            technique = test_sim.labour._farming_technique()
            baseline_fte = test_sim.labour._expected_year_farm_need(
                test_sim.labour._share_farm_fte(adult_equivalent, technique),
                adult_equivalent, technique)
            total_hours = (test_sim.population.working_age
                           * labour_allocation.HOURS_PER_FARM_WORKER_YEAR)
            wanted_share = min(baseline_fte * labour_allocation.HOURS_PER_FARM_WORKER_YEAR,
                               total_hours) / total_hours
            test_sim._demographic_recovery(test_sim.civ.get("year", 100) + 1)
            hours = test_sim.state.economy.society_labour_hours
            farm_share = hours[labour_allocation.FARM_TRADE] / sum(hours.values())
            self.assertGreater(farm_share, 0.0)
            self.assertLess(farm_share, 1.0)
            self.assertAlmostEqual(farm_share, wanted_share, delta=0.02, msg=civ["id"])

    def test_yearly_allocation_continues_from_the_spun_up_split(self):
        test_sim, first = self._first_year("rome_100ad")
        first = dict(first)
        test_sim._demographic_recovery(102)
        second = test_sim.state.economy.society_labour_hours
        rest_first = {trade: hours for trade, hours in first.items()
                      if trade != labour_allocation.FARM_TRADE}
        rest_second = {trade: hours for trade, hours in second.items()
                       if trade != labour_allocation.FARM_TRADE}
        total_first, total_second = sum(rest_first.values()), sum(rest_second.values())
        for trade, hours in rest_first.items():
            self.assertAlmostEqual(hours / total_first, rest_second[trade] / total_second,
                                   delta=0.02)

    def test_a_short_harvest_still_pulls_hours_to_the_farm(self):
        test_sim, hours = self._first_year("rome_100ad")
        farm = labour_allocation.FARM_TRADE
        before = hours[farm]
        for trade in hours:
            hours[trade] *= 0.5 if trade == farm else 1.0
        test_sim._demographic_recovery(102)
        self.assertGreater(test_sim.state.economy.society_labour_hours[farm], before * 0.5)


if __name__ == "__main__":
    unittest.main()
