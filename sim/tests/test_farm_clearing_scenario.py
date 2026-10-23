"""Scenario: clearing in a game. A short civilisation clears more ground over the years, and the rent the solver prices
and the incumbent price tables follow it. The rules (the ladder, the hands clearing is paid in, the ceiling, the rent's
margin, a fed farm not clearing) are in test_farm_clearing; the cleared area's save and load is the generic state round
trip."""
import unittest

from .harness import *  # noqa: F401,F403
from sim.labour import labour_allocation
from sim.geography.api import crop_site, tiles_held
from sim.world import agriculture, land


def _ladder(civ_id):
    civ = S.load_civ(civ_id)
    share = 1.0 - agriculture.DEFAULT_ROTATION.fallow_share_of_holding
    return land.territory_cropland({tile: crop_site(tile, share) for tile in tiles_held(civ)})


class ClearingTests(unittest.TestCase):
    def _run(self, civ_id, years, scale=1.0):
        test_sim = unopened_sim(civ_id, events=False)
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
        test_sim = unopened_sim("han_china_100ad", events=False)
        before = test_sim._price_tables()[0]["hectare_land"]
        test_sim.farm_land.hectares *= 3.0
        after = test_sim._price_tables()[0]["hectare_land"]
        self.assertNotAlmostEqual(before, after, places=6)


if __name__ == "__main__":
    unittest.main()
