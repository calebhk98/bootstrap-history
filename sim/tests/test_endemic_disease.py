"""Endemic disease is a tile layer derived from climate and vegetation (Complaint 540): a tile in the tsetse belt
cannot keep cattle or horses and offers no draught team, a temperate tile is unaffected, malaria raises mortality
on a hot wet tile against a cool dry one, and no engine code names a region."""
QUICK_TOPIC = True
import os
import types
import unittest

from sim.living_stock.api import stock_rates
from sim.living_stock.module import LivingStock
from sim.tests import module_harness
from sim.geography import api as geography
from sim.geography.api import Geography
from sim.geography import endemic, food_pasture
from sim.world.endemic_deaths import endemic_excess_deaths

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BELT_TILE = "nigeria_03"       # hot, wet, wooded savanna
TEMPERATE_TILE = "france_02"   # cool, moist
COOL_DRY_TILE = "ukraine_04"
SAHEL_TILE = "burkina_faso_02"  # inside the box, too dry for the vector


def holder(world_map, place):
    """The living-stock module standing at `place`, whose geography answers the endemic loss of a species there."""
    land = Geography(types.SimpleNamespace(world_map=world_map))
    return module_harness.build(LivingStock, views={"stock_land": {"place": place, "pasture_kg": 0.0},
                                                    "endemic_stock_loss": land.endemic_stock_loss}), land


class EndemicDiseaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world_map = geography.open_map()

    def herd_ids(self, tile):
        return {herd for _source, herd, _kcal in food_pasture.herd_contributions(self.world_map, tile)}

    def test_files_are_sound(self):
        self.assertEqual(geography.endemic_problems(), [])

    def test_the_vector_follows_climate_and_cover_inside_its_range(self):
        challenge = lambda tile: endemic.challenge(self.world_map, tile, "trypanosomiasis")
        self.assertEqual(challenge(BELT_TILE), 1.0)
        self.assertEqual(challenge(TEMPERATE_TILE), 0.0)
        self.assertLess(challenge(SAHEL_TILE), 0.01)

    def test_a_belt_tile_cannot_keep_cattle_or_horses_and_a_temperate_tile_can(self):
        self.assertNotIn("cattle", self.herd_ids(BELT_TILE))
        self.assertNotIn("horse", self.herd_ids(BELT_TILE))
        self.assertIn("cattle", self.herd_ids(TEMPERATE_TILE))
        self.assertEqual(geography.endemic_animal_loss(TEMPERATE_TILE, ("cattle", "horse"), self.world_map), 0.0)

    def test_hosts_not_listed_are_unaffected(self):
        self.assertEqual(endemic.host_loss(self.world_map, BELT_TILE, "goat"), {})

    def test_a_belt_tile_offers_no_draught_team_and_a_temperate_tile_does(self):
        rates = stock_rates()["draught_animal_kg"]
        (belt, belt_land), (temperate, temperate_land) = holder(self.world_map, BELT_TILE), holder(self.world_map, TEMPERATE_TILE)
        self.assertEqual(belt.endemic_keeping("draught_animal_kg"), 0.0)
        self.assertEqual(temperate.endemic_keeping("draught_animal_kg"), 1.0)
        self.assertGreater(belt_land.endemic_stock_loss(BELT_TILE, rates.get("species")), rates["natural_increase"])
        self.assertEqual(temperate_land.endemic_stock_loss(TEMPERATE_TILE, rates.get("species")), 0.0)

    def test_malaria_raises_mortality_on_a_hot_wet_tile_against_a_cool_dry_one(self):
        hot = geography.endemic_people_loss([BELT_TILE], self.world_map)
        cool = geography.endemic_people_loss([COOL_DRY_TILE], self.world_map)
        self.assertGreater(hot["children"], 0.0)
        self.assertEqual(cool.get("children", 0.0), 0.0)

    def test_a_band_dies_at_the_endemic_rate_cut_by_the_disease_burden(self):
        self.assertAlmostEqual(endemic_excess_deaths(300.0, 10.0, 0.1, 1.0), 30.0)
        self.assertAlmostEqual(endemic_excess_deaths(300.0, 10.0, 0.1, 0.5), 15.0)

    def test_a_removed_disease_burden_removes_the_excess_death_rate(self):
        self.assertEqual(endemic_excess_deaths(300.0, 10.0, 0.1, 0.0), 0.0)

    def test_no_endemic_rate_adds_no_deaths(self):
        self.assertEqual(endemic_excess_deaths(300.0, 10.0, 0.0, 1.0), 0.0)

    def test_the_excess_is_never_more_than_the_bands_survivors(self):
        self.assertEqual(endemic_excess_deaths(300.0, 290.0, 0.5, 1.0), 10.0)



if __name__ == "__main__":
    unittest.main()
