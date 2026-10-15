"""A named district with no endowment is sized by the map's geological model, not left to name no site."""

QUICK_TOPIC = True

import unittest

from sim.geography import map_source, queries, resources_catalogue, resources_district, resources_endowment
from sim.tests.test_geography_resources import small_map, with_resources

DISTRICT = {"id": "named_district", "name": "Named District", "resource": "gold", "lat": 36.0, "lon": 14.0,
            "deposit_type": "vein", "status": "historic", "source": "fixture", "conf": "D"}


def map_with(world_map, *rows):
    deposits = dict(world_map.catalogue("deposits"))
    deposits.update({row["id"]: row for row in rows})
    return map_source.WorldMap(world_map.map_id, world_map.tiles, world_map.layers,
                               dict(world_map.catalogues, deposits=deposits), world_map.folders)


def site(world_map, deposit_id="named_district", year=0):
    rows = queries.worked_deposits(["b2"], "gold", year, (), world_map)
    return next(row for row in rows if row["id"] == deposit_id)


class DistrictSizeTests(unittest.TestCase):
    def setUp(self):
        self.base = small_map()
        self.entry = resources_catalogue.resource(self.base, "gold")

    def test_an_unsized_district_of_a_defined_type_takes_that_types_expected_size(self):
        world_map = map_with(self.base, DISTRICT)
        vein = next(deposit_type for deposit_type in self.entry["deposit_types"] if deposit_type["id"] == "vein")
        expected_kg = resources_endowment.expected_contained_per_deposit(world_map, self.entry, vein)
        row = site(world_map)
        self.assertAlmostEqual(row["size_tonnes"], expected_kg / 1000.0)
        self.assertEqual(row["size_basis"], "expected_for_deposit_type:vein")

    def test_an_unsized_district_of_an_undefined_type_takes_the_mean_over_the_minerals_types(self):
        world_map = map_with(self.base, dict(DISTRICT, deposit_type="no_such_type"))
        types = self.entry["deposit_types"]
        weight = sum(deposit_type["deposits_per_million_km2"] for deposit_type in types)
        expected_kg = sum(deposit_type["deposits_per_million_km2"] / weight
                          * resources_endowment.expected_contained_per_deposit(world_map, self.entry, deposit_type)
                          for deposit_type in types)
        row = site(world_map)
        self.assertAlmostEqual(row["size_tonnes"], expected_kg / 1000.0)
        self.assertEqual(row["size_basis"], "expected_across_types_of:gold")

    def test_a_stated_endowment_is_kept_over_the_expectation(self):
        row = site(map_with(self.base, dict(DISTRICT, endowment=7.0, endowment_unit="tonnes_contained")))
        self.assertAlmostEqual(row["size_tonnes"], 7.0)
        self.assertEqual(row["size_basis"], "catalogue")

    def test_the_tiles_crustal_ceiling_bounds_the_expectation(self):
        thin = dict(self.entry, crustal_abundance_ppm=1e-12)
        world_map = map_with(with_resources(self.base, dict(self.base.catalogue("resources"), gold=thin)), DISTRICT)
        ceiling_kg = resources_endowment.crustal_ceiling(world_map, "b2", thin)
        self.assertLess(ceiling_kg, 1.0)
        self.assertAlmostEqual(site(world_map)["size_tonnes"], ceiling_kg / 1000.0)

    def test_a_row_sized_by_the_empire_output_model_is_left_for_that_model(self):
        world_map = map_with(self.base, dict(DISTRICT, share_of_empire_output=0.1))
        self.assertIsNone(site(world_map)["size_tonnes"])
        self.assertIsNone(resources_district.district_quantity(
            world_map, next(row for row in resources_catalogue.known_deposits(world_map, "gold")
                            if row["id"] == "named_district"))[0])

    def test_a_dated_unsized_district_is_worked_before_the_start_and_drawn_down(self):
        world_map = map_with(self.base, dict(DISTRICT, first_worked=-400))
        mined = queries.mined_before(["b2"], "gold", 0, world_map)
        working = next(working for working in mined["workings"] if working["id"] == "named_district")
        self.assertGreater(working["mined_share"], 0.0)
        self.assertLess(working["mined_share"], 1.0)
        self.assertNotIn("named_district", mined["unworked"])


if __name__ == "__main__":
    unittest.main()
