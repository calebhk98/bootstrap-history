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

    def test_the_same_seed_gives_the_same_starting_workforce(self):
        first = sim(civ="rome_100ad", events=False)
        second = sim(civ="rome_100ad", events=False)
        for test_sim in (first, second):
            test_sim._demographic_recovery(101)
        self.assertEqual(first.state.economy.society_labour_hours,
                         second.state.economy.society_labour_hours)


class HoursRuleTests(unittest.TestCase):
    """The yearly split of hours, called with plain inputs."""
    farm = labour_allocation.FARM_TRADE
    year = labour_allocation.HOURS_PER_FARM_WORKER_YEAR

    def test_the_society_hours_split_by_the_shares_and_add_up_to_the_total(self):
        hours = labour_allocation.society_hours(1000.0, 400.0, {"smith": 0.25, "weaver": 0.75})
        self.assertEqual(hours, {self.farm: 400.0, "smith": 150.0, "weaver": 450.0})
        self.assertAlmostEqual(sum(hours.values()), 1000.0)

    def test_the_farm_never_takes_more_than_all_the_hours(self):
        hours = labour_allocation.society_hours(1000.0, 5000.0, {"smith": 1.0})
        self.assertEqual(hours, {self.farm: 1000.0, "smith": 0.0})

    def test_an_opening_with_no_held_split_starts_the_farm_at_the_food_balance(self):
        self.assertEqual(labour_allocation.current_farm_hours({}, 1.0e6, 100.0), 100.0 * self.year)

    def test_an_opening_whose_food_balance_needs_more_hands_than_there_are_starts_the_farm_at_all_the_hours(self):
        self.assertEqual(labour_allocation.current_farm_hours({}, 1.0e6, 1.0e9), 1.0e6)

    def test_a_held_split_keeps_its_farm_share_of_this_years_hours(self):
        held = {self.farm: 30.0, "smith": 70.0}
        self.assertAlmostEqual(labour_allocation.current_farm_hours(held, 2000.0, 1.0e9), 600.0)

    def test_a_shortfall_with_land_to_spare_calls_for_more_farm_workers(self):
        technique = labour_allocation.farming_technique.DEFAULT_TECHNIQUE
        gross_kg_per_hour = 100.0   # well above the seed an hour's hectares need, so a hand adds food
        self.assertGreater(labour_allocation.net_marginal_product_kg_per_hour(gross_kg_per_hour, technique), 0.0)
        wanted = labour_allocation.farm_workers_needed(100.0, 100.0, 1000.0, gross_kg_per_hour, 1.0e9, technique=technique)
        self.assertGreater(wanted, 100.0)

    def test_a_shortfall_never_calls_for_more_workers_than_the_land_holds(self):
        technique = labour_allocation.farming_technique.DEFAULT_TECHNIQUE
        per_worker = labour_allocation.agriculture.hectares_cropped_per_farm_worker(technique.crop, technique.toolkit)
        wanted = labour_allocation.farm_workers_needed(100.0, 100.0, 1.0e12, 10.0, 50.0 * per_worker, technique=technique)
        self.assertAlmostEqual(wanted, 50.0)

    def test_hours_move_toward_the_farm_when_it_is_needed_for_more_and_away_when_for_less(self):
        self.assertGreater(labour_allocation.farm_hours_after(100.0, 200.0, 1000.0), 100.0)
        self.assertLess(labour_allocation.farm_hours_after(100.0, 50.0, 1000.0), 100.0)
        self.assertEqual(labour_allocation.farm_hours_after(100.0, 100.0, 1000.0), 100.0)


class EngineStartTests(unittest.TestCase):

    def _first_year(self, civ_id):
        test_sim = sim(civ=civ_id, events=False)
        test_sim._demographic_recovery(test_sim.civ.get("year", 100) + 1)
        return test_sim, test_sim.state.economy.society_labour_hours

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
