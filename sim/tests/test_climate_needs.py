"""sim/world/climate_needs.py: warmth, clothing and shelter floors calculated from climate (unittest-style)."""
import json
import os
import unittest

from sim.world import climate_needs
from sim.world.climate_needs import floors_for_civilisation_tiles, floors_for_tile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _tile(class_code, latitude, mix=None):
    record = {"lat": latitude, "koppen_class": class_code}
    if mix:
        record["koppen_sample_mix"] = mix
    return record


def _load(relative):
    with open(os.path.join(ROOT, relative), encoding="utf-8") as handle:
        return json.load(handle)


class ClimateOrderingTests(unittest.TestCase):
    def test_cold_tile_needs_more_of_everything_than_warm(self):
        warm = floors_for_tile(_tile("Af", 5))
        for cold_tile in (_tile("Dfc", 62), _tile("ET", 70), _tile("Dfb", 50)):
            cold = floors_for_tile(cold_tile)
            for name in warm:
                self.assertGreater(cold[name], warm[name], (cold_tile, name))

    def test_tropical_tile_needs_no_heating(self):
        for class_code in ("Af", "Am", "Aw", "As"):
            self.assertEqual(floors_for_tile(_tile(class_code, 15))["warmth_mj"], 0.0)

    def test_monotone_in_coldest_month(self):
        warmth, clothing, shelter = [], [], []
        for coldest in range(25, -40, -5):
            warmest = max(coldest, 15)
            warmth.append(climate_needs.warmth_delivered_mj(coldest, warmest))
            clothing.append(climate_needs.clothing_kg_per_year(coldest))
            shelter.append(climate_needs.shelter_m3_per_year(coldest))
        for series in (warmth, clothing, shelter):
            self.assertEqual(series, sorted(series))

    def test_walls_follow_temperature_not_civilisation(self):
        self.assertLess(climate_needs.wall_thickness_metres(22.0),
                        climate_needs.wall_thickness_metres(0.0))
        self.assertLess(climate_needs.wall_thickness_metres(0.0),
                        climate_needs.wall_thickness_metres(-25.0))

    def test_clothing_never_below_minimum_covering(self):
        floor = (climate_needs.MINIMUM_COVERING_CLO * climate_needs.CLOTH_KILOGRAMS_PER_CLO_PER_PERSON
                 / climate_needs.GARMENT_SERVICE_LIFE_YEARS)
        self.assertGreaterEqual(floors_for_tile(_tile("Af", 0))["clothing_kg"], floor - 1e-12)

    def test_sample_mix_is_a_weighted_average_of_class_floors(self):
        cold, warm = floors_for_tile(_tile("Dfc", 60)), floors_for_tile(_tile("Cfb", 60))
        mixed = floors_for_tile(_tile("Dfc", 60, {"Dfc": 1, "Cfb": 3}))
        self.assertAlmostEqual(mixed["warmth_mj"], 0.25 * cold["warmth_mj"] + 0.75 * warm["warmth_mj"])

    def test_deterministic(self):
        tile = _tile("Csa", 42, {"Csa": 3, "BSk": 1})
        self.assertEqual(floors_for_tile(tile), floors_for_tile(dict(tile)))


class RealTerritoryTests(unittest.TestCase):
    """Region lookups below are test scaffolding: they only choose which tiles to compute."""

    @classmethod
    def setUpClass(cls):
        cls.geography = _load("data/world/geography.json")
        region_to_tiles = cls.geography["land_tiles"]["region_to_tiles"]
        cls.floors = {}
        for civilisation_id in ("norse_900ad", "england_1300", "rome_100ad", "mexica_1500"):
            regions = _load("data/civilizations/%s.json" % civilisation_id)["home_regions"]
            tile_ids = sorted({tile for region in regions for tile in region_to_tiles.get(region, ())})
            cls.floors[civilisation_id] = floors_for_civilisation_tiles(cls.geography, tile_ids)["weighted_mean"]

    def test_warmth_orders_norse_england_rome_mexica(self):
        warmth = {civilisation: floors["warmth_mj"] for civilisation, floors in self.floors.items()}
        self.assertGreater(warmth["norse_900ad"], warmth["england_1300"])
        self.assertGreater(warmth["england_1300"], warmth["rome_100ad"])
        self.assertGreaterEqual(warmth["rome_100ad"], warmth["mexica_1500"])

    def test_clothing_and_shelter_follow_the_same_order(self):
        for name in ("clothing_kg", "shelter_m3"):
            self.assertGreater(self.floors["norse_900ad"][name], self.floors["england_1300"][name])
            self.assertGreaterEqual(self.floors["england_1300"][name], self.floors["mexica_1500"][name])

    def test_population_weights_move_the_mean(self):
        tiles = self.geography["land_tiles"]["tiles"]
        cold_id = next(tile_id for tile_id, tile in sorted(tiles.items()) if tile["koppen_class"] == "Dfc")
        warm_id = next(tile_id for tile_id, tile in sorted(tiles.items()) if tile["koppen_class"] == "Af")
        mostly_warm = floors_for_civilisation_tiles(self.geography, [cold_id, warm_id], {cold_id: 1, warm_id: 9})
        mostly_cold = floors_for_civilisation_tiles(self.geography, [cold_id, warm_id], {cold_id: 9, warm_id: 1})
        self.assertGreater(mostly_cold["weighted_mean"]["warmth_mj"], mostly_warm["weighted_mean"]["warmth_mj"])


if __name__ == "__main__":
    unittest.main()
