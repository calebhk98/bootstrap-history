"""The farm model at its edges, the rules that need no game: unfarmable ground on the clearing ladder, pinned as
properties (direction and bounds), never an exact number. Barren land, land below subsistence, the technology that
rescues it and surplus farm labour are in test_farm_subsistence_rules."""
QUICK_TOPIC = True

import unittest

from sim.geography.api import crop_site, tiles_held
from sim.tests.harness import S
from sim.world import agriculture, land

CIV_ID = "rome_100ad"


def sites_with_fertility(fertility_of_tile):
    """The held tiles' crop sites where each tile's yield factor is `fertility_of_tile(rank, tile_count)`,
    rank 0 being the best tile."""
    share = 1.0 - agriculture.DEFAULT_ROTATION.fallow_share_of_holding
    sites = {tile_id: crop_site(tile_id, share) for tile_id in set(tiles_held(S.load_civ(CIV_ID)))}
    ranked = sorted(sites, key=lambda tile_id: (-sites[tile_id].yield_factor, tile_id))
    return {tile_id: sites[tile_id]._replace(yield_factor=fertility_of_tile(rank, len(ranked)))
            for rank, tile_id in enumerate(ranked)}


class ClearingLadderTests(unittest.TestCase):
    def test_unfarmable_parcels_are_not_arable_ground(self):
        sites = sites_with_fertility(lambda rank, count: 0.0 if rank >= count // 2 else 0.8)
        territory = land.territory_cropland(sites)
        self.assertTrue(territory.ladder)
        self.assertTrue(all(fertility > 0.0 for fertility, _hectares in territory.ladder))
        self.assertAlmostEqual(sum(hectares for _f, hectares in territory.ladder), territory.cropped_hectares, places=3)
        self.assertAlmostEqual(territory.mean_yield_factor, 0.8, places=6)

    def test_ground_with_no_farmable_tile_is_empty_not_an_error(self):
        territory = land.territory_cropland(sites_with_fertility(lambda _rank, _count: 0.0))
        self.assertEqual(territory.ladder, [])
        self.assertEqual(territory.cropped_hectares, 0.0)

    def test_the_arable_ceiling_the_farm_clears_toward_is_only_the_farmable_ground(self):
        sites = sites_with_fertility(lambda rank, count: 0.0 if rank >= count // 2 else 0.5)
        territory = land.territory_cropland(sites)
        farmable = sum(site.cropped_hectares for site in sites.values() if site.yield_factor > 0.0)
        self.assertAlmostEqual(territory.cropped_hectares, farmable, places=3)
        self.assertGreater(land.ladder_quality(territory.ladder, territory.cropped_hectares), 0.0)


if __name__ == "__main__":
    unittest.main()
