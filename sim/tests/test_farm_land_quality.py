"""Each civilisation's farm sits on its own soil and climate: land quality is the cropped-area-weighted yield factor (soil,
climate, river water; geography's crop_site) of the tiles it holds, and the farm is sized so the starting population is
still fed on that ground.

Rules, each called on inputs built from geography's tiles or by the test, with no game:

1. `land.territory_cropland` / `land.ladder_quality` give the hand-computed weighted mean of the best ground, for three
   civilisations and for a mod civilisation of one region; the civilisations differ.
2. A civilisation naming no known region holds no tile and is refused (`require_territory`).
3. `agriculture.gross_harvest_kg` responds to land quality; `farmland_for_population` never passes the arable ceiling.
"""
QUICK_TOPIC = True

import unittest

from sim.land.rules import require_territory
from sim.geography.api import crop_site, tiles_held, tiles_of_regions
from sim.tests.harness import S
from sim.world import agriculture, land

OPEN_FIELD_SHARE = 1.0 - agriculture.DEFAULT_ROTATION.fallow_share_of_holding
CIVILISATIONS = ("rome_100ad", "han_china_100ad", "norse_900ad")


def sites_of(tile_ids):
    return {tile_id: crop_site(tile_id, OPEN_FIELD_SHARE) for tile_id in tile_ids}


def expected_quality(tile_ids, hectares=None):
    """Mean yield factor of the best `hectares` of cropland (all of it when None), computed tile by tile."""
    sites = sites_of(tile_ids)
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
    def test_quality_is_the_weighted_mean_of_the_best_ground_the_civilisation_holds(self):
        for civ_id in CIVILISATIONS:
            held = tiles_held(S.load_civ(civ_id))
            territory = land.territory_cropland(sites_of(held))
            for share in (0.1, 0.5, 1.0):
                hectares = territory.cropped_hectares * share
                self.assertAlmostEqual(land.ladder_quality(territory.ladder, hectares),
                                       expected_quality(held, hectares), places=9, msg=civ_id)

    def test_the_whole_ceiling_has_the_mean_yield_of_all_the_cropland(self):
        for civ_id in CIVILISATIONS:
            held = tiles_held(S.load_civ(civ_id))
            self.assertAlmostEqual(land.territory_cropland(sites_of(held)).mean_yield_factor,
                                   expected_quality(held), places=9, msg=civ_id)

    def test_civilisations_differ(self):
        qualities = {civ_id: land.territory_cropland(sites_of(tiles_held(S.load_civ(civ_id)))).mean_yield_factor
                     for civ_id in CIVILISATIONS}
        self.assertEqual(len({round(value, 6) for value in qualities.values()}), len(CIVILISATIONS))
        self.assertLess(qualities["norse_900ad"], qualities["han_china_100ad"])

    def test_a_single_region_mod_civ_gets_the_mean_of_that_regions_tiles(self):
        held = tiles_of_regions(["scandinavia"])
        territory = land.territory_cropland(sites_of(held))
        self.assertAlmostEqual(land.ladder_quality(territory.ladder, territory.cropped_hectares * 0.5),
                               expected_quality(held, territory.cropped_hectares * 0.5))

    def test_region_without_land_data_holds_no_tile_and_is_refused(self):
        civ = {"id": "mod_nowhere", "home_regions": ["no_such_region_anywhere"]}
        self.assertEqual(list(tiles_held(civ)), [])
        with self.assertRaises(ValueError):
            require_territory(civ, tiles_held(civ))

    def test_farm_output_responds_to_quality(self):
        land_at = lambda quality: agriculture.Land(5000.0, quality)
        self.assertGreater(agriculture.gross_harvest_kg(land_at(1.2), labour_hours=1.0e9),
                           agriculture.gross_harvest_kg(land_at(1.0), labour_hours=1.0e9))

    def test_farm_never_exceeds_arable_ceiling(self):
        for civ_id in CIVILISATIONS:
            ceiling = land.territory_cropland(sites_of(tiles_held(S.load_civ(civ_id)))).cropped_hectares
            sized = agriculture.farmland_for_population(1.0e12, arable_hectares_ceiling=ceiling)
            self.assertLessEqual(sized.hectares, ceiling + 1e-6, civ_id)

    def test_a_small_population_is_fed_on_less_than_the_ceiling(self):
        sized = agriculture.farmland_for_population(1000.0, arable_hectares_ceiling=1.0e9)
        self.assertLess(sized.hectares, 1.0e9)


if __name__ == "__main__":
    unittest.main()
