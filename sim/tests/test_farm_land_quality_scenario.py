"""Scenario: in a game the farm is sized on the soil and climate of the civilisation's own tiles (its quality is the weighted
mean of the best ground the starting population needs, never past the arable ceiling), a civilisation naming no land data
is refused at construction, and a good run of years does not release the farm's hands below the food balance. The rules
are in test_farm_land_quality."""
import copy
import unittest

from .harness import *  # noqa: F401,F403
from sim.geography.api import crop_site, tiles_held, tiles_of_regions
from sim.labour import labour_allocation
from sim.world import agriculture

OPEN_FIELD_SHARE = 1.0 - agriculture.DEFAULT_ROTATION.fallow_share_of_holding
_CIVILISATIONS = ("rome_100ad", "han_china_100ad", "norse_900ad")
_SIZED_GAMES = {}


def _sized_game(civ_id):
    """One game per civilisation for the tests that only read the farm; the farm is sized before the economy opens."""
    if civ_id not in _SIZED_GAMES:
        _SIZED_GAMES[civ_id] = unopened_sim(civ_id)
    return _SIZED_GAMES[civ_id]


def _expected_quality(sites, hectares):
    """Mean yield of the best `hectares` of `sites`, the game's own (they carry the toolkit's tillage capacity and the soil nitrogen stock)."""
    ranked = sorted((tile_id for tile_id, site in sites.items() if site.yield_factor > 0.0 and site.cropped_hectares > 0.0),
                    key=lambda tile_id: (-sites[tile_id].yield_factor, tile_id))
    remaining, taken, weighted = hectares, 0.0, 0.0
    for tile_id in ranked:
        step = min(sites[tile_id].cropped_hectares, remaining)
        taken += step
        weighted += step * sites[tile_id].yield_factor
        remaining -= step
        if remaining <= 0.0:
            break
    return weighted / taken


class FarmSizingTests(unittest.TestCase):
    def test_game_farm_quality_is_the_weighted_mean_of_the_ground_it_covers(self):
        for civ_id in _CIVILISATIONS:
            test_sim = _sized_game(civ_id)
            self.assertAlmostEqual(test_sim.farm_land.quality,
                                   _expected_quality(test_sim.farm_sites(), test_sim.farm_land.hectares),
                                   places=9, msg=civ_id)

    def test_game_farm_never_exceeds_the_arable_ceiling(self):
        for civ_id in _CIVILISATIONS:
            test_sim = _sized_game(civ_id)
            cropland = sum(crop_site(tile_id, OPEN_FIELD_SHARE).cropped_hectares for tile_id in tiles_held(test_sim.civ))
            self.assertLessEqual(test_sim.farm_land.hectares, cropland + 1e-6, civ_id)

    def test_single_region_mod_civ_farm_has_the_mean_of_that_regions_tiles(self):
        civ = copy.deepcopy(S.load_civ("rome_100ad"))
        civ["id"] = "mod_single_region"
        civ.pop("home_tiles", None)
        civ["home_regions"] = ["scandinavia"]
        test_sim = build_unopened(lambda: S.Sim(NODES, ORDER, random.Random(1), events=False, manual=True, civ=civ))
        self.assertEqual(set(test_sim.farm_sites()), set(tiles_of_regions(["scandinavia"])))
        self.assertAlmostEqual(test_sim.farm_land.quality,
                               _expected_quality(test_sim.farm_sites(), test_sim.farm_land.hectares))

    def test_region_without_land_data_fails_loudly(self):
        civ = copy.deepcopy(S.load_civ("rome_100ad"))
        civ.pop("home_tiles", None)
        civ["home_regions"] = ["no_such_region_anywhere"]
        with self.assertRaises(ValueError):     # no tiles to farm, so no territory for the economy
            S.Sim(NODES, ORDER, random.Random(1), events=False, manual=True, civ=civ)


class FoodBalanceWorkforceTests(unittest.TestCase):
    def test_workers_are_not_released_below_the_food_balance_after_a_good_year(self):
        test_sim = sim("norse_900ad", events=False)
        test_sim.farm_land.hectares *= 100.0
        share_fte = agriculture.farm_workers_fte_for_population(
            test_sim._adult_equivalent_population(test_sim.population))
        for year in range(101, 111):
            test_sim._demographic_recovery(year)
        hours = test_sim.state.economy.society_labour_hours[labour_allocation.FARM_TRADE]
        fte = hours / labour_allocation.HOURS_PER_FARM_WORKER_YEAR
        self.assertGreater(fte, 1.05 * share_fte * test_sim.population.total / test_sim.civ["population"])


if __name__ == "__main__":
    unittest.main()
