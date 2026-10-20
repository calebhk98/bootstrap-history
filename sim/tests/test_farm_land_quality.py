"""Each civilisation's farm sits on its own soil and climate: land quality is the cropped-area-weighted yield factor
(soil, climate, river water; geography's crop_site) of the tiles it holds, and the farm is sized so the starting
population is still fed on that ground."""
from sim.geography.api import crop_site, tiles_held, tiles_of_regions
import copy
import os
import unittest

from .harness import *  # noqa: F401,F403
from sim.world import agriculture
from sim.labour import labour_allocation

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OPEN_FIELD_SHARE = 1.0 - agriculture.DEFAULT_ROTATION.fallow_share_of_holding

_CIVILISATIONS = ("rome_100ad", "han_china_100ad", "norse_900ad")

_READ_ONLY_GAMES = {}


def _game(civ_id):
    """One game per civilisation for the tests that only read the farm."""
    if civ_id not in _READ_ONLY_GAMES:
        _READ_ONLY_GAMES[civ_id] = sim(civ_id)
    return _READ_ONLY_GAMES[civ_id]


def _cropped_hectares(tile_id):
    return crop_site(tile_id, OPEN_FIELD_SHARE).cropped_hectares


def _expected_quality(held_tiles, hectares=None):
    """Mean yield factor of the best `hectares` of cropland (all of it when None), hand-computed from the tiles."""
    sites = {tile_id: crop_site(tile_id, OPEN_FIELD_SHARE) for tile_id in held_tiles}
    ranked = sorted((tile_id for tile_id, site in sites.items() if site.yield_factor > 0.0 and site.cropped_hectares > 0.0),
                    key=lambda tile_id: (-sites[tile_id].yield_factor, tile_id))
    remaining = float("inf") if hectares is None else hectares
    taken = weighted = 0.0
    for tile_id in ranked:
        step = min(sites[tile_id].cropped_hectares, remaining)
        taken += step
        weighted += step * sites[tile_id].yield_factor
        remaining -= step
        if remaining <= 0.0:
            break
    return weighted / taken


class FarmLandQualityTests(unittest.TestCase):
    def test_quality_matches_weighted_average_of_own_regions(self):
        for civ_id in _CIVILISATIONS:
            civ = S.load_civ(civ_id)
            test_sim = _game(civ_id)
            expected = _expected_quality(tiles_held(civ), test_sim.farm_land.hectares)
            self.assertAlmostEqual(test_sim.farm_land.quality, expected, places=9, msg=civ_id)

    def test_civilisations_differ(self):
        qualities = {civ_id: _game(civ_id).farm_land.quality for civ_id in _CIVILISATIONS}
        self.assertEqual(len(set(round(value, 6) for value in qualities.values())), len(_CIVILISATIONS))
        self.assertLess(qualities["norse_900ad"], qualities["han_china_100ad"])

    def test_single_region_mod_civ_gets_the_mean_of_that_regions_tiles(self):
        civ = copy.deepcopy(S.load_civ("rome_100ad"))
        civ["id"] = "mod_single_region"
        civ.pop("home_tiles", None)
        civ["home_regions"] = ["scandinavia"]
        test_sim = build_unopened(
            lambda: S.Sim(NODES, ORDER, random.Random(1), events=False, manual=True, civ=civ))   # the farm is sized before the economy opens
        self.assertAlmostEqual(
            test_sim.farm_land.quality,
            _expected_quality(tiles_of_regions(["scandinavia"]), test_sim.farm_land.hectares))

    def test_region_without_land_data_fails_loudly(self):
        civ = copy.deepcopy(S.load_civ("rome_100ad"))
        civ.pop("home_tiles", None)
        civ["home_regions"] = ["no_such_region_anywhere"]
        with self.assertRaises(ValueError):     # no tiles to farm, so no territory for the economy
            S.Sim(NODES, ORDER, random.Random(1), events=False, manual=True, civ=civ)

    def test_farm_output_responds_to_quality(self):
        for civ_id in ("rome_100ad",):
            test_sim = _game(civ_id)
            harvest = agriculture.gross_harvest_kg(test_sim.farm_land, labour_hours=1.0e9)
            better = agriculture.gross_harvest_kg(
                agriculture.Land(test_sim.farm_land.hectares,
                                 test_sim.farm_land.quality * 1.2), labour_hours=1.0e9)
            self.assertGreater(better, harvest)

    def test_farm_never_exceeds_arable_ceiling(self):
        for civ_id in _CIVILISATIONS:
            test_sim = _game(civ_id)
            cropland = sum(_cropped_hectares(tile_id) for tile_id in tiles_held(test_sim.civ))
            self.assertLessEqual(test_sim.farm_land.hectares, cropland + 1e-6)


class FoodBalanceWorkforceTests(unittest.TestCase):
    """Soil only changes yield; the labour market pulls workers to the farm."""

    def _farm_fte(self, quality, year):
        test_sim = sim("norse_900ad", events=False)
        test_sim.farm_land.quality = quality
        test_sim.farm_land.hectares *= 100.0  # land is not the limit here
        test_sim._demographic_recovery(year)
        hours = test_sim.state.economy.society_labour_hours[labour_allocation.FARM_TRADE]
        return hours / labour_allocation.HOURS_PER_FARM_WORKER_YEAR

    def test_poorer_soil_pulls_more_workers_onto_the_farm_at_the_start(self):
        self.assertGreater(self._farm_fte(0.5, 101), self._farm_fte(1.0, 101))

    def test_workers_are_not_released_below_the_food_balance_after_a_good_year(self):
        test_sim = sim("norse_900ad", events=False)
        test_sim.farm_land.hectares *= 100.0
        share_fte = agriculture.farm_workers_fte_for_population(
            test_sim._adult_equivalent_population(test_sim.population))
        for year in range(101, 111):
            test_sim._demographic_recovery(year)
        hours = test_sim.state.economy.society_labour_hours[labour_allocation.FARM_TRADE]
        fte = hours / labour_allocation.HOURS_PER_FARM_WORKER_YEAR
        self.assertGreater(fte, 1.05 * share_fte * test_sim.population.total
                           / test_sim.civ["population"])

    def test_farm_workers_are_capped_by_farm_area_plus_what_is_clearable(self):
        test_sim = sim("norse_900ad", events=False)
        test_sim.farm_land.hectares *= 0.5
        cap = ((test_sim.farm_land.hectares
                + test_sim.labour._clearable_hectares()
                * agriculture.CLEARING_LABOUR_HOURS_PER_HECTARE
                / labour_allocation.HOURS_PER_FARM_WORKER_YEAR
                * agriculture.hectares_cropped_per_farm_worker())
               / agriculture.hectares_cropped_per_farm_worker())
        test_sim._demographic_recovery(101)
        hours = test_sim.state.economy.society_labour_hours[labour_allocation.FARM_TRADE]
        self.assertLessEqual(hours / labour_allocation.HOURS_PER_FARM_WORKER_YEAR, cap * 1.0001)


if __name__ == "__main__":
    unittest.main()
