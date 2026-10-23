"""Endemic disease is a tile layer derived from climate and vegetation (Complaint 540): a tile in the tsetse belt
cannot keep cattle or horses and offers no draught team, a temperate tile is unaffected, malaria raises mortality
on a hot wet tile against a cool dry one, and no engine code names a region."""
QUICK_TOPIC = True
import os
import re
import types
import unittest

from sim.engine.living_stock_growth import LivingStockGrowthMixin
from sim.engine.living_stock_opening import LivingStockOpeningMixin
from sim.engine.living_stock_yearly import stock_rates
from sim.geography import api as geography
from sim.geography.api import Geography
from sim.geography import endemic, food_pasture
from sim.world.demography import Population

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BELT_TILE = "nigeria_03"       # hot, wet, wooded savanna
TEMPERATE_TILE = "france_02"   # cool, moist
COOL_DRY_TILE = "ukraine_04"
SAHEL_TILE = "burkina_faso_02"  # inside the box, too dry for the vector


class Holder(LivingStockOpeningMixin, LivingStockGrowthMixin):
    def __init__(self, world_map, place):
        self.world_map, self._place = world_map, place
        self.geography = Geography(types.SimpleNamespace(world_map=world_map))

    def stock_place(self):
        return self._place


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
        belt, temperate = Holder(self.world_map, BELT_TILE), Holder(self.world_map, TEMPERATE_TILE)
        self.assertEqual(belt.endemic_keeping("draught_animal_kg"), 0.0)
        self.assertEqual(temperate.endemic_keeping("draught_animal_kg"), 1.0)
        self.assertGreater(belt.endemic_stock_loss(rates), rates["natural_increase"])
        self.assertEqual(temperate.endemic_stock_loss(rates), 0.0)

    def test_malaria_raises_mortality_on_a_hot_wet_tile_against_a_cool_dry_one(self):
        hot = geography.endemic_people_loss([BELT_TILE], self.world_map)
        cool = geography.endemic_people_loss([COOL_DRY_TILE], self.world_map)
        self.assertGreater(hot["children"], 0.0)
        self.assertEqual(cool.get("children", 0.0), 0.0)
        food = 2500.0 * 1000.0

        def deaths(rates):
            people = Population(children=300.0, working_age=600.0, elderly=100.0)
            return people.step(food, endemic_death_rates=rates).deaths

        self.assertGreater(deaths(hot), deaths(cool))
        self.assertEqual(deaths(cool), deaths(None))

    def test_a_removed_disease_burden_removes_the_excess_death_rate(self):
        people = Population(children=300.0, working_age=600.0, elderly=100.0)
        other = Population(children=300.0, working_age=600.0, elderly=100.0)
        rates = {"children": 0.1}
        with_rates = people.step(2500.0 * 1000.0, disease_burden=0.0, endemic_death_rates=rates).deaths
        self.assertEqual(with_rates, other.step(2500.0 * 1000.0, disease_burden=0.0).deaths)

    def test_no_engine_code_names_a_region(self):
        names = re.compile(r"africa|sahel|nigeria|congo|sahara", re.IGNORECASE)
        for relative in ("sim/geography/endemic.py", "sim/geography/food_pasture.py",
                         "sim/engine/living_stock_growth.py", "sim/engine/living_stock_opening.py",
                         "sim/engine/living_stock_yearly.py", "sim/engine/disease_port.py"):
            with open(os.path.join(ROOT, relative), encoding="utf-8") as handle:
                self.assertIsNone(names.search(handle.read()), relative)


if __name__ == "__main__":
    unittest.main()
