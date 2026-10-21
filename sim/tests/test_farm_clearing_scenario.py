"""Scenario: clearing in a game. A short civilisation clears more ground over the years, the new ground follows the
best-first ladder, a fed civilisation does not clear, the cleared area survives a save and load, and the rent the solver
prices and the incumbent price tables follow it. The rules (the ladder, the hands clearing is paid in, the ceiling, the
rent's margin) are in test_farm_clearing."""
import os
import tempfile
import unittest

from .harness import *  # noqa: F401,F403
from sim.labour import labour_allocation
from sim.geography.api import crop_site, tiles_held
from sim.engine import saveload
from sim.world import agriculture, land


def _ladder(civ_id):
    civ = S.load_civ(civ_id)
    share = 1.0 - agriculture.DEFAULT_ROTATION.fallow_share_of_holding
    return land.territory_cropland({tile: crop_site(tile, share) for tile in tiles_held(civ)})


class ClearingTests(unittest.TestCase):
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
        ceiling = _ladder("han_china_100ad").cropped_hectares
        small = self._rent(civ, ceiling * 0.02)
        large = self._rent(civ, ceiling * 0.6)
        self.assertNotAlmostEqual(small, large, places=6)

    def test_the_incumbent_price_tables_follow_the_cleared_area(self):
        test_sim = sim("han_china_100ad", events=False)
        before = test_sim._price_tables()[0]["hectare_land"]
        test_sim.farm_land.hectares *= 3.0
        after = test_sim._price_tables()[0]["hectare_land"]
        self.assertNotAlmostEqual(before, after, places=6)


if __name__ == "__main__":
    unittest.main()
