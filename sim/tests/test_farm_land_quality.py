"""Each civilisation's farm sits on its own soil: land quality is the
arable-area-weighted fertility of the regions it holds, and the farm is
sized so the starting population is still fed on that soil."""
import copy
import json
import os
import unittest

from .harness import *  # noqa: F401,F403
from sim.world import agriculture
from sim.labour import labour_allocation

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
with open(os.path.join(_ROOT, "data", "world", "geography.json"), encoding="utf-8") as _handle:
    _GEOGRAPHY = json.load(_handle)
_TILES = _GEOGRAPHY["land_tiles"]["tiles"]
_REGION_TO_TILES = _GEOGRAPHY["land_tiles"]["region_to_tiles"]

_CIVILISATIONS = ("rome_100ad", "han_china_100ad", "england_1300",
                  "mexica_1500", "norse_900ad")


def _held_tiles(home_regions):
    return sorted({tile_id for region in home_regions
                   for tile_id in _REGION_TO_TILES[region]})


def _arable_km2(tile_id):
    tile = _TILES[tile_id]
    return tile["land_area_km2"] * tile["arable_fraction"]


def _expected_quality(home_regions, hectares=None):
    """Mean fertility of the best `hectares` of arable ground (all of it when
    None), hand-computed from the tiles."""
    tile_ids = sorted(_held_tiles(home_regions),
                      key=lambda tile_id: (-_TILES[tile_id]["fertility_quality_multiplier"], tile_id))
    remaining = float("inf") if hectares is None else hectares
    taken = weighted = 0.0
    for tile_id in tile_ids:
        step = min(100.0 * _arable_km2(tile_id), remaining)
        taken += step
        weighted += step * _TILES[tile_id]["fertility_quality_multiplier"]
        remaining -= step
        if remaining <= 0.0:
            break
    return weighted / taken


class FarmLandQualityTests(unittest.TestCase):
    def test_quality_matches_weighted_average_of_own_regions(self):
        for civ_id in _CIVILISATIONS:
            civ = S.load_civ(civ_id)
            test_sim = sim(civ_id)
            expected = _expected_quality(civ["home_regions"], test_sim.farm_land.hectares)
            self.assertAlmostEqual(test_sim.farm_land.quality, expected, places=9, msg=civ_id)

    def test_civilisations_differ(self):
        qualities = {civ_id: sim(civ_id).farm_land.quality for civ_id in _CIVILISATIONS}
        self.assertGreater(len(set(round(value, 6) for value in qualities.values())), 3)
        self.assertLess(qualities["norse_900ad"], qualities["han_china_100ad"])

    def test_single_region_mod_civ_gets_the_mean_of_that_regions_tiles(self):
        civ = copy.deepcopy(S.load_civ("rome_100ad"))
        civ["id"] = "mod_single_region"
        civ["home_regions"] = ["scandinavia"]
        test_sim = S.Sim(NODES, ORDER, random.Random(1), events=False, manual=True, civ=civ)
        self.assertAlmostEqual(
            test_sim.farm_land.quality,
            _expected_quality(["scandinavia"], test_sim.farm_land.hectares))

    def test_region_without_land_data_fails_loudly(self):
        civ = copy.deepcopy(S.load_civ("rome_100ad"))
        civ["home_regions"] = ["no_such_region_anywhere"]
        with self.assertRaises(KeyError):
            S.Sim(NODES, ORDER, random.Random(1), events=False, manual=True, civ=civ)

    def test_farm_output_responds_to_quality(self):
        for civ_id in ("rome_100ad", "norse_900ad"):
            test_sim = sim(civ_id)
            harvest = agriculture.gross_harvest_kg(test_sim.farm_land, labour_hours=1.0e9)
            better = agriculture.gross_harvest_kg(
                agriculture.Land(test_sim.farm_land.hectares,
                                 test_sim.farm_land.quality * 1.2), labour_hours=1.0e9)
            self.assertGreater(better, harvest)

    def test_farm_never_exceeds_arable_ceiling(self):
        for civ_id in _CIVILISATIONS:
            test_sim = sim(civ_id)
            arable_hectares = 100.0 * sum(
                _arable_km2(tile_id)
                for tile_id in _held_tiles(test_sim.civ["home_regions"]))
            self.assertLessEqual(test_sim.farm_land.hectares, arable_hectares + 1e-6)


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
