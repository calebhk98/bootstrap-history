"""Complaint 537: the tile's crop capacity is the farm model's harvest on the tile's own land.

The farm model owns the yield of a cropped hectare (crop, tools, rotation, storage loss); geography owns the tile's
cropped hectares and its yield factor (soil, climate, river water). The tile view and the farm model must agree on a
tile's harvest, and a better tool or rotation must raise the tile's capacity as it raises the farm's harvest."""
QUICK_TOPIC = True

import unittest

from sim.engine.data import load_civ
from sim.geography.api import crop_site, food_potential, open_map, tiles_held
from sim.world import agriculture, agriculture_tile, farming_technique

RELATIVE_TOLERANCE = 1e-6


def _farm_net_kcal(technique, hectares_cropped, yield_factor):
    """The farm model's own harvest of `hectares_cropped` at `yield_factor`, net of seed and storage loss, in kcal."""
    crop, toolkit = technique.crop, technique.toolkit
    per_worker = agriculture.hectares_cropped_per_farm_worker(crop, toolkit)
    gross_kg = agriculture.gross_harvest_kg(
        agriculture.Land(hectares_cropped, quality=yield_factor), hectares_cropped * farming_technique.hours_per_hectare(technique),
        crop=crop, toolkit=toolkit, rotation=technique.rotation, worker_count=hectares_cropped / per_worker)
    seed_kg = crop.planting_material_kg_per_ha * hectares_cropped
    loss_kg = gross_kg * agriculture.DEFAULT_STORAGE_TECHNIQUE.spoilage_rate_per_year
    return max(0.0, gross_kg - seed_kg - loss_kg) * crop.energy_kcal_per_kg


def _toolkit_with_better_ploughing(multiplier):
    return farming_technique.DEFAULT_TECHNIQUE._replace(
        toolkit=agriculture.DEFAULT_TOOLKIT._replace(ploughing_yield_multiplier=multiplier))


class TileCropCapacityIsTheFarmHarvestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world_map = open_map()
        cls.tiles = [tile for tile in tiles_held(load_civ("rome_100ad"), cls.world_map)
                     if crop_site(tile, 0.5, cls.world_map).yield_factor > 0.0]

    def _tile_crop_kcal(self, tile, technique):
        view = food_potential(tile, None, self.world_map, None, agriculture_tile.crop_technique(technique))
        return view["kcal_per_year"].get("crops", 0.0)

    def _techniques(self):
        base = farming_technique.DEFAULT_TECHNIQUE
        three_field = agriculture.Rotation(name="three_field", fallow_share_of_holding=1.0 / 3.0, soil_fertility_yield_multiplier=1.0)
        return [base, _toolkit_with_better_ploughing(base.toolkit.ploughing_yield_multiplier * 1.2), base._replace(rotation=three_field)]

    def test_every_held_tile_agrees_with_the_farm_model_on_its_harvest_under_each_technique(self):
        self.assertTrue(self.tiles)
        for technique in self._techniques():
            share = 1.0 - technique.rotation.fallow_share_of_holding
            for tile in self.tiles:
                site = crop_site(tile, share, self.world_map)
                expected = _farm_net_kcal(technique, site.cropped_hectares, site.yield_factor)
                self.assertAlmostEqual(self._tile_crop_kcal(tile, technique), expected, delta=RELATIVE_TOLERANCE * max(expected, 1.0), msg=tile)

    def test_soils_and_climates_differ_between_tiles(self):
        factors = {round(crop_site(tile, 0.5, self.world_map).yield_factor, 3) for tile in self.tiles}
        self.assertGreater(len(factors), 3)

    def test_a_better_plough_raises_every_tiles_capacity(self):
        base, better, _three_field = self._techniques()
        for tile in self.tiles:
            self.assertGreaterEqual(self._tile_crop_kcal(tile, better), self._tile_crop_kcal(tile, base), tile)
        self.assertGreater(sum(self._tile_crop_kcal(tile, better) for tile in self.tiles),
                           sum(self._tile_crop_kcal(tile, base) for tile in self.tiles))

    def test_a_rotation_that_fallows_less_crops_more_of_each_open_field(self):
        base = farming_technique.DEFAULT_TECHNIQUE
        rotation = agriculture.Rotation(name="three_field", fallow_share_of_holding=1.0 / 3.0, soil_fertility_yield_multiplier=1.0)
        three_field = base._replace(rotation=rotation)
        tile = max(self.tiles, key=lambda candidate: crop_site(candidate, 0.5, self.world_map).cropped_hectares)
        self.assertGreater(self._tile_crop_kcal(tile, three_field), self._tile_crop_kcal(tile, base))

    def test_no_technique_means_no_crop_source(self):
        view = food_potential(self.tiles[0], None, self.world_map)
        self.assertNotIn("crops", view["kcal_per_year"])


if __name__ == "__main__":
    unittest.main()
