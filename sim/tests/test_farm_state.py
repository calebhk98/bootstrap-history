"""The agriculture module owns the farm's cleared ground, ladder, ceiling, opening area and the year's technique: each command
sets one fact, each view reads it, and the saved part survives a save and a load. The module is built over plain values."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.agriculture.commands import RecordOpeningFarm, SetFarmLand, SetFarmTechnique, SetFarmTerritory
from sim.agriculture.state import AgricultureWorld
from sim.engine.state import deserialize_state, serialize_state
from sim.tests import agriculture_stand_in
from sim.world import agriculture as farm_rules
from sim.world.farming_technique import DEFAULT_TECHNIQUE


def farm(**views):
    return agriculture_stand_in.build(views=views)


class LandTests(unittest.TestCase):
    def test_setting_the_land_is_read_back_as_hectares_and_quality(self):
        module = farm()
        module.set_farm_land(SetFarmLand(120.0, 0.9))
        land = module.farm_land()
        self.assertEqual((land.hectares, land.quality), (120.0, 0.9))

    def test_a_negative_area_is_refused_and_leaves_the_land_as_it_was(self):
        module = farm()
        module.set_farm_land(SetFarmLand(50.0, 1.1))
        with self.assertRaises(ValueError):
            module.set_farm_land(SetFarmLand(-1.0, 1.0))
        self.assertEqual(module.farm_land().hectares, 50.0)


class TerritoryTests(unittest.TestCase):
    def test_the_ladder_and_ceiling_are_what_was_set(self):
        module = farm()
        module.set_farm_territory(SetFarmTerritory([(1.1, 100.0), (0.8, 50.0)], 150.0))
        self.assertEqual((module.farm_ladder(), module.farm_arable_ceiling()), ([(1.1, 100.0), (0.8, 50.0)], 150.0))

    def test_before_the_territory_is_set_there_is_no_ceiling(self):
        self.assertIsNone(farm().farm_arable_ceiling())


class OpeningTests(unittest.TestCase):
    def test_the_opening_area_is_the_ground_cleared_when_it_was_recorded_and_stays_after_more_is_cleared(self):
        module = farm()
        module.set_farm_land(SetFarmLand(80.0, 1.0))
        module.record_opening_farm(RecordOpeningFarm())
        module.set_farm_land(SetFarmLand(95.0, 1.0))
        self.assertEqual(module.opening_farmed_hectares(), 80.0)

    def test_before_the_opening_is_recorded_there_is_none(self):
        self.assertIsNone(farm().opening_farmed_hectares())


class TechniqueTests(unittest.TestCase):
    def test_the_year_starts_on_the_default_technique(self):
        self.assertIs(farm().farm_technique_this_year(), DEFAULT_TECHNIQUE)

    def test_the_technique_chosen_is_the_one_read(self):
        module = farm()
        module.set_farm_technique(SetFarmTechnique("chosen"))
        self.assertEqual(module.farm_technique_this_year(), "chosen")


class FoodDemandTests(unittest.TestCase):
    def test_demand_is_the_adult_equivalents_times_one_persons_yearly_grain_for_the_crop(self):
        people = SimpleNamespace(children=0.0, working_age=1000.0, elderly=0.0)
        module = farm(population=people)
        self.assertEqual(module.farm_food_demand_kg(),
                         1000.0 * farm_rules.annual_food_demand_kg_per_person(DEFAULT_TECHNIQUE.crop))


class SaveTests(unittest.TestCase):
    def test_the_land_ladder_ceiling_and_opening_area_survive_a_save_and_a_load(self):
        world = AgricultureWorld(cleared_hectares=70.0, cleared_quality=0.95, ladder=[(1.1, 40.0), (0.7, 30.0)],
                                 arable_ceiling=70.0, opening_farmed_hectares=60.0)
        again = deserialize_state(serialize_state(world), AgricultureWorld)
        self.assertEqual((again.cleared_hectares, again.cleared_quality, again.ladder, again.arable_ceiling,
                          again.opening_farmed_hectares), (70.0, 0.95, [(1.1, 40.0), (0.7, 30.0)], 70.0, 60.0))

    def test_the_years_technique_is_not_saved_and_a_loaded_game_starts_on_the_default(self):
        world = AgricultureWorld(technique_this_year="chosen")
        serialized = serialize_state(world)
        self.assertNotIn("technique_this_year", serialized)
        self.assertIs(deserialize_state(serialized, AgricultureWorld).technique_this_year, DEFAULT_TECHNIQUE)


if __name__ == "__main__":
    unittest.main()
