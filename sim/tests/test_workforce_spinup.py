"""The starting workforce per trade comes from a spin-up of the labour
market, not from authored shares."""
import copy
import glob
import json
import os
import tempfile
import unittest

from .harness import *  # noqa: F401,F403
from sim.labour import labour_allocation
from sim.engine.catalog import load_production_catalog
from sim.solve_prices_core import techniques_available_to
from sim.world import agriculture
from sim.labour import workforce_spinup

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CIV_PATHS = sorted(glob.glob(os.path.join(_ROOT, "data", "civilizations", "*.json")))
_PRODUCTION = load_production_catalog(_ROOT)


def _civilisations():
    for path in _CIV_PATHS:
        with open(path, encoding="utf-8") as handle:
            civ = json.load(handle)
        if civ.get("id"):
            yield civ


def _trades_of_available_recipes(production, reached):
    available, _unreached, _unclassified = techniques_available_to(production, reached)
    trades = set()
    for entry in available.values():
        trades.update(entry.get("labour_hours") or {})
        for capital in entry.get("capital") or ():
            trades.update(capital.get("build_labour_hours") or {})
    return trades


class SpinUpTests(unittest.TestCase):

    def test_converges_for_every_base_civilisation(self):
        for civ in _civilisations():
            result = workforce_spinup.spin_up(_PRODUCTION, set(civ["starting_techs"]))
            self.assertTrue(result.converged, civ["id"])
            self.assertLessEqual(result.years, workforce_spinup.SPIN_UP_MAX_YEARS)
            self.assertAlmostEqual(sum(result.shares_by_trade.values()), 1.0, places=9)

    def test_stops_early_when_the_split_stops_moving(self):
        civ = next(_civilisations())
        result = workforce_spinup.spin_up(_PRODUCTION, set(civ["starting_techs"]))
        self.assertLess(result.years, workforce_spinup.SPIN_UP_MAX_YEARS)
        self.assertLessEqual(result.final_share_change,
                             workforce_spinup.SPIN_UP_SHARE_TOLERANCE)

    def test_too_short_a_spin_up_reports_not_converged(self):
        civ = next(_civilisations())
        result = workforce_spinup.spin_up(_PRODUCTION, set(civ["starting_techs"]),
                                          max_years=1)
        self.assertFalse(result.converged)
        self.assertEqual(result.years, 1)

    def test_every_available_trade_gets_workers_and_no_other_does(self):
        farm_trade = labour_allocation.FARM_TRADE
        for civ in _civilisations():
            reached = set(civ["starting_techs"])
            result = workforce_spinup.spin_up(_PRODUCTION, reached)
            expected = _trades_of_available_recipes(_PRODUCTION, reached) - {farm_trade}
            self.assertEqual({trade for trade, share in result.shares_by_trade.items()
                              if share > 0.0}, expected, civ["id"])
            self.assertTrue(all(share >= 0.0 for share in result.shares_by_trade.values()))

    def test_civilisations_with_different_technology_split_differently(self):
        splits = [workforce_spinup.spin_up(_PRODUCTION, set(civ["starting_techs"])).shares_by_trade
                  for civ in _civilisations()]
        self.assertGreater(len({tuple(sorted(split)) for split in splits}), 1)

    def test_a_mod_trade_with_an_available_recipe_gets_workers(self):
        production = copy.deepcopy(_PRODUCTION)
        production["zz_gadget"] = {
            "outputs": {"zz_gadget": 1.0}, "inputs": {"iron_bar_kg": 0.5},
            "labour_hours": {"zz_wright": 3.0}, "requires_node": None,
            "basis": "one gadget", "yield_basis": "test", "conf": "C"}
        production["zz_locked"] = {
            "outputs": {"zz_locked": 1.0}, "inputs": {},
            "labour_hours": {"zz_sage": 3.0}, "requires_node": "zz_unreached_node",
            "basis": "one locked", "yield_basis": "test", "conf": "C"}
        civ = next(_civilisations())
        result = workforce_spinup.spin_up(production, set(civ["starting_techs"]))
        self.assertGreater(result.shares_by_trade.get("zz_wright", 0.0), 0.0)
        self.assertEqual(result.shares_by_trade.get("zz_sage", 0.0), 0.0)
        # The wright also draws iron, so the smith side of the graph is busier.
        base = workforce_spinup.spin_up(_PRODUCTION, set(civ["starting_techs"]))
        self.assertNotEqual(base.shares_by_trade, result.shares_by_trade)

    def test_deterministic_for_a_given_input(self):
        civ = next(_civilisations())
        first = workforce_spinup.spin_up(_PRODUCTION, set(civ["starting_techs"]))
        second = workforce_spinup.spin_up(_PRODUCTION, set(civ["starting_techs"]))
        self.assertEqual(first.shares_by_trade, second.shares_by_trade)
        self.assertEqual(first.years, second.years)

    def test_the_same_seed_gives_the_same_starting_workforce(self):
        first = sim(civ="rome_100ad", events=False)
        second = sim(civ="rome_100ad", events=False)
        for test_sim in (first, second):
            test_sim._demographic_recovery(101)
        self.assertEqual(first.state.economy.society_labour_hours,
                         second.state.economy.society_labour_hours)

    def test_cache_round_trips_and_is_keyed_by_the_inputs(self):
        civ = next(_civilisations())
        reached = set(civ["starting_techs"])
        with tempfile.TemporaryDirectory() as cache_dir:
            fresh = workforce_spinup.cached_spin_up(_PRODUCTION, reached, cache_dir=cache_dir)
            self.assertEqual(len(os.listdir(cache_dir)), 1)
            workforce_spinup.forget_in_process_cache()
            again = workforce_spinup.cached_spin_up(_PRODUCTION, reached, cache_dir=cache_dir)
            self.assertEqual(fresh.shares_by_trade, again.shares_by_trade)
            production = copy.deepcopy(_PRODUCTION)
            production["zz_gadget"] = {
                "outputs": {"zz_gadget": 1.0}, "inputs": {},
                "labour_hours": {"zz_wright": 3.0}, "requires_node": None}
            workforce_spinup.cached_spin_up(production, reached, cache_dir=cache_dir)
            self.assertEqual(len(os.listdir(cache_dir)), 2)

    def test_default_cache_location_is_not_tracked_data(self):
        ignored = open(os.path.join(_ROOT, ".gitignore"), encoding="utf-8").read().split()
        top = os.path.relpath(workforce_spinup.DEFAULT_CACHE_DIRECTORY, _ROOT).split(os.sep)[0]
        self.assertTrue(any(line.strip("/") == top for line in ignored), top)


class EngineStartTests(unittest.TestCase):

    def _first_year(self, civ_id):
        test_sim = sim(civ=civ_id, events=False)
        test_sim._demographic_recovery(test_sim.civ.get("year", 100) + 1)
        return test_sim, test_sim.state.economy.society_labour_hours

    def test_start_workforce_is_split_by_trade_not_pooled(self):
        for civ in _civilisations():
            _test_sim, hours = self._first_year(civ["id"])
            expected = _trades_of_available_recipes(
                _PRODUCTION, set(civ["starting_techs"])) | {labour_allocation.FARM_TRADE}
            self.assertEqual({trade for trade, value in hours.items() if value > 0.0},
                             expected, civ["id"])

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
