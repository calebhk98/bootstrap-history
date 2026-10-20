"""The farm model at its edges, the rules that need no game: unfarmable ground on the clearing ladder, and the allocator
sizing the farm from the harvest of an extra hour net of the seed that hour's hectares need. Each is pinned as a property
(direction and bounds), never an exact number. The game runs (barren land, land below subsistence, the technology that
rescues it, surplus farm labour) are `test_farm_edges_scenario`."""
QUICK_TOPIC = True

import unittest

from sim.geography.api import crop_site, tiles_held
from sim.labour import labour_allocation
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
        self.assertEqual(labour_allocation.cleared_hectares(1e12, 0.0, territory.cropped_hectares),
                         territory.cropped_hectares)
        self.assertGreater(land.ladder_quality(territory.ladder, territory.cropped_hectares), 0.0)


class NetMarginalProductTests(unittest.TestCase):
    """The allocator sizes the farm from the harvest of an extra hour net of the seed that hour's hectares need."""

    def setUp(self):
        self.technique = labour_allocation.farming_technique.DEFAULT_TECHNIQUE
        self.seed_per_hour = (
            self.technique.crop.planting_material_kg_per_ha
            / labour_allocation.farming_technique.hours_per_hectare(self.technique))

    def _need(self, gross_per_hour, shortfall_kg=1e6, clearable_hectares=1e4):
        return labour_allocation.farm_workers_needed(
            10.0, 10.0, shortfall_kg, gross_per_hour, 100.0,
            clearable_hectares=clearable_hectares, technique=self.technique)

    def test_net_product_is_gross_less_seed_the_hour_needs(self):
        net = labour_allocation.net_marginal_product_kg_per_hour(
            self.seed_per_hour * 3.0 * agriculture.LABOUR_OUTPUT_ELASTICITY, self.technique)
        self.assertAlmostEqual(net, self.seed_per_hour * 2.0)

    def test_seed_eating_land_does_not_draw_hands_with_the_shortfall(self):
        gross = self.seed_per_hour * 0.5 * agriculture.LABOUR_OUTPUT_ELASTICITY
        self.assertEqual(self._need(gross, 1.0), self._need(gross, 1e9))
        self.assertLessEqual(self._need(gross), 10.0)

    def test_seed_eating_land_is_not_cleared(self):
        gross = self.seed_per_hour * 0.5 * agriculture.LABOUR_OUTPUT_ELASTICITY
        self.assertEqual(self._need(gross, clearable_hectares=1e4), self._need(gross, clearable_hectares=0.0))

    def test_land_that_pays_for_its_seed_still_draws_hands_and_clearing(self):
        gross = self.seed_per_hour * 5.0 * agriculture.LABOUR_OUTPUT_ELASTICITY
        self.assertGreater(self._need(gross, 1e3, clearable_hectares=0.0), 10.0)
        self.assertGreater(self._need(gross, 1e9, clearable_hectares=1e4), self._need(gross, 1e9, clearable_hectares=0.0))

    def test_surplus_frees_more_hands_when_the_net_product_is_smaller(self):
        def freed(gross):
            return 10.0 - labour_allocation.farm_workers_needed(
                10.0, 10.0, 0.0, gross, 1e6, surplus_kg=1e3, technique=self.technique)
        self.assertGreater(freed(self.seed_per_hour * 1.5 * agriculture.LABOUR_OUTPUT_ELASTICITY),
                           freed(self.seed_per_hour * 5.0 * agriculture.LABOUR_OUTPUT_ELASTICITY))


if __name__ == "__main__":
    unittest.main()
