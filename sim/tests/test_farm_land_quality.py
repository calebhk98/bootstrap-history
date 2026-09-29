"""Each civilisation's farm sits on its own soil: land quality is the
arable-area-weighted fertility of the regions it holds, and the farm is
sized so the starting population is still fed on that soil."""
import copy
import json
import os
import unittest

from .harness import *  # noqa: F401,F403
from sim.world import agriculture

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
with open(os.path.join(_ROOT, "data", "world", "geography.json"), encoding="utf-8") as _handle:
    _REGIONS = json.load(_handle)["regions"]

_CIVILISATIONS = ("rome_100ad", "han_china_100ad", "england_1300",
                  "mexica_1500", "norse_900ad")


def _expected_quality(home_regions):
    total_area = 0.0
    weighted = 0.0
    for region in home_regions:
        land = _REGIONS[region]["land"]
        arable = land["land_area_km2"] * land["arable_fraction"]
        total_area += arable
        weighted += arable * land["fertility_quality_multiplier"]
    return weighted / total_area


class FarmLandQualityTests(unittest.TestCase):
    def test_quality_matches_weighted_average_of_own_regions(self):
        for civ_id in _CIVILISATIONS:
            civ = S.load_civ(civ_id)
            expected = _expected_quality(civ["home_regions"])
            self.assertAlmostEqual(sim(civ_id).farm_land.quality, expected, places=9, msg=civ_id)

    def test_civilisations_differ(self):
        qualities = {civ_id: sim(civ_id).farm_land.quality for civ_id in _CIVILISATIONS}
        self.assertGreater(len(set(round(value, 6) for value in qualities.values())), 3)
        self.assertLess(qualities["norse_900ad"], qualities["han_china_100ad"])

    def test_single_region_mod_civ_gets_that_regions_quality(self):
        civ = copy.deepcopy(S.load_civ("rome_100ad"))
        civ["id"] = "mod_single_region"
        civ["home_regions"] = ["scandinavia"]
        test_sim = S.Sim(NODES, ORDER, random.Random(1), events=False, manual=True, civ=civ)
        self.assertAlmostEqual(test_sim.farm_land.quality,
                               _REGIONS["scandinavia"]["land"]["fertility_quality_multiplier"])

    def test_region_without_land_data_fails_loudly(self):
        civ = copy.deepcopy(S.load_civ("rome_100ad"))
        civ["home_regions"] = ["no_such_region_anywhere"]
        with self.assertRaises(KeyError):
            S.Sim(NODES, ORDER, random.Random(1), events=False, manual=True, civ=civ)

    def test_poorer_soil_farms_more_ground_and_starts_fed(self):
        rome = sim("rome_100ad")
        norse = sim("norse_900ad")
        per_head_rome = rome.farm_land.hectares / rome.civ["population"]
        per_head_norse = norse.farm_land.hectares / norse.civ["population"]
        self.assertGreater(per_head_norse, per_head_rome)
        for test_sim in (rome, norse):
            harvest = agriculture.gross_harvest_kg(
                test_sim.farm_land, labour_hours=1.0e9)
            better = agriculture.gross_harvest_kg(
                agriculture.Land(test_sim.farm_land.hectares,
                                 test_sim.farm_land.quality * 1.2), labour_hours=1.0e9)
            self.assertGreater(better, harvest)

    def test_farm_never_exceeds_arable_ceiling(self):
        for civ_id in _CIVILISATIONS:
            test_sim = sim(civ_id)
            arable_hectares = 100.0 * sum(
                _REGIONS[region]["land"]["land_area_km2"]
                * _REGIONS[region]["land"]["arable_fraction"]
                for region in test_sim.civ["home_regions"])
            self.assertLessEqual(test_sim.farm_land.hectares, arable_hectares + 1e-6)


if __name__ == "__main__":
    unittest.main()
