"""The farmed area grows toward the arable ceiling, best ground first, paid
for in labour and driven by food scarcity; land rent reads the same ladder."""
import copy
import os
import tempfile
import unittest

from .harness import *  # noqa: F401,F403
from sim.labour import labour_allocation
from sim.engine.core import load_geography
from sim.engine import saveload
from sim.world import agriculture, land

HOURS = labour_allocation.HOURS_PER_FARM_WORKER_YEAR


def _ladder(civ_id):
    civ = S.load_civ(civ_id)
    return land.territory_farmland(civ["home_regions"], load_geography())


class LadderTests(unittest.TestCase):
    def test_ladder_is_best_ground_first_and_sums_to_the_ceiling(self):
        territory = _ladder("norse_900ad")
        fertilities = [fertility for fertility, _hectares in territory.ladder]
        self.assertEqual(fertilities, sorted(fertilities, reverse=True))
        self.assertAlmostEqual(sum(hectares for _f, hectares in territory.ladder),
                               territory.arable_hectares, places=3)

    def test_quality_falls_as_worse_ground_is_brought_in(self):
        territory = _ladder("han_china_100ad")
        ceiling = territory.arable_hectares
        qualities = [land.ladder_quality(territory.ladder, ceiling * share)
                     for share in (0.05, 0.2, 0.5, 1.0)]
        self.assertEqual(qualities, sorted(qualities, reverse=True))
        self.assertAlmostEqual(qualities[-1], territory.mean_fertility, places=9)


class RentReadsTheFarmedAreaTests(unittest.TestCase):
    def test_margin_is_the_last_ground_the_farm_covers(self):
        civ_id = "han_china_100ad"
        territory = _ladder(civ_id)
        small = land.margin_outcome_for_civilization(
            civ_id, farmed_hectares=territory.arable_hectares * 0.02)
        large = land.margin_outcome_for_civilization(
            civ_id, farmed_hectares=territory.arable_hectares * 0.6)
        self.assertGreater(small.margin_fertility_quality_multiplier,
                           large.margin_fertility_quality_multiplier)
        supplied = sum(a.arable_hectares_supplied for a in large.allocations)
        self.assertAlmostEqual(
            supplied, territory.arable_hectares * 0.6,
            delta=territory.arable_hectares * 0.01)


class ClearingTests(unittest.TestCase):
    def test_labour_cost_is_a_declared_labelled_parameter(self):
        self.assertGreater(agriculture.CLEARING_LABOUR_HOURS_PER_HECTARE, 0.0)

    def _run(self, civ_id, years, scale=1.0):
        test_sim = sim(civ_id, events=False)
        test_sim.farm_land.hectares *= scale
        history = []
        for year in range(101, 101 + years):
            before = test_sim.farm_land.hectares
            test_sim._demographic_recovery(year)
            history.append((before, test_sim.farm_land.hectares))
        return test_sim, history

    def test_a_short_civilisation_clears_more_ground(self):
        test_sim, history = self._run("norse_900ad", 30)
        self.assertGreater(test_sim.farm_land.hectares, history[0][0] * 1.05)

    def test_area_never_passes_the_arable_ceiling(self):
        test_sim, _history = self._run("norse_900ad", 60)
        ceiling = _ladder("norse_900ad").arable_hectares
        self.assertLessEqual(test_sim.farm_land.hectares, ceiling + 1e-6)

    def test_new_ground_is_worse_than_the_ground_already_farmed(self):
        test_sim = sim("norse_900ad", events=False)
        quality_before = test_sim.farm_land.quality
        for year in range(101, 131):
            test_sim._demographic_recovery(year)
        # Cleared ground comes from the best-first ladder, so quality never rises.
        self.assertLessEqual(test_sim.farm_land.quality, quality_before)
        expected = land.ladder_quality(_ladder("norse_900ad").ladder,
                                       test_sim.farm_land.hectares)
        self.assertAlmostEqual(test_sim.farm_land.quality, expected, places=9)

    def test_clearing_is_paid_in_hands_beyond_what_the_farm_can_crop(self):
        test_sim = sim("norse_900ad", events=False)
        for year in range(101, 111):
            hectares_before = test_sim.farm_land.hectares
            test_sim._demographic_recovery(year)
            hectares_cleared = test_sim.farm_land.hectares - hectares_before
            hours = test_sim.state.economy.society_labour_hours[labour_allocation.FARM_TRADE]
            crop_hours = (hectares_before
                          / agriculture.hectares_cropped_per_farm_worker()) * HOURS
            spare_hours = max(0.0, hours - crop_hours)
            self.assertLessEqual(
                hectares_cleared * agriculture.CLEARING_LABOUR_HOURS_PER_HECTARE,
                spare_hours * 1.0001 + 1e-6, year)

    def test_a_fed_civilisation_does_not_clear(self):
        test_sim = sim("rome_100ad", events=False)
        test_sim.farm_land.quality = 1.5
        test_sim.farm_land.hectares *= 1.5
        start = test_sim.farm_land.hectares
        test_sim._demographic_recovery(101)
        self.assertAlmostEqual(test_sim.farm_land.hectares, start, delta=start * 1e-9)

    def test_cleared_area_survives_save_and_load(self):
        test_sim = sim("norse_900ad", events=False)
        for year in range(101, 111):
            test_sim._demographic_recovery(year)
        path = tempfile.mktemp(suffix=".json")
        try:
            saveload.save_state(test_sim, path)
            fresh = sim("norse_900ad", events=False)
            saveload.load_state(fresh, path)
        finally:
            if os.path.exists(path):
                os.remove(path)
        self.assertAlmostEqual(fresh.farm_land.hectares, test_sim.farm_land.hectares, places=6)
        self.assertAlmostEqual(fresh.farm_land.quality, test_sim.farm_land.quality, places=9)


class PriceCacheFollowsClearingTests(unittest.TestCase):
    def _rent(self, civ, farmed_hectares):
        from sim.engine import prices
        from sim.engine.data import schedule_of_civilisation
        document = schedule_of_civilisation(civ).document()
        solved = prices.solved_prices(
            civ["starting_techs"], document, civilization=civ, farmed_hectares=farmed_hectares)
        return solved.prices_in_labour_hours["hectare_land"]

    def test_clearing_land_changes_the_rent_the_solver_prices(self):
        civ = S.load_civ("han_china_100ad")
        ceiling = _ladder("han_china_100ad").arable_hectares
        small = self._rent(civ, ceiling * 0.02)
        large = self._rent(civ, ceiling * 0.6)
        self.assertNotAlmostEqual(small, large, places=6)

    def test_the_incumbent_price_tables_follow_the_cleared_area(self):
        test_sim = sim("han_china_100ad", events=False)
        before = test_sim._price_tables()[0]["hectare_land"]
        test_sim.farm_land.hectares *= 3.0
        after = test_sim._price_tables()[0]["hectare_land"]
        self.assertNotAlmostEqual(before, after, places=6)

    def test_nearby_areas_share_one_solve(self):
        from sim.engine import prices
        self.assertEqual(prices.band_farmed_hectares(1000.0), prices.band_farmed_hectares(1001.0))
        self.assertNotEqual(prices.band_farmed_hectares(1000.0), prices.band_farmed_hectares(2000.0))


if __name__ == "__main__":
    unittest.main()
