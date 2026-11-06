"""Complaints 57 and 58: the cohort model is the only population, and a civilisation's farming technique reaches yield, labour and
literacy through the labour market rather than through side scalars.

The technique is read by `Labour` over a stand-in world (the tree's own farming declarations), and the food, labour and
literacy rules are called as functions; no game is built. The decades-long runs (food and mechanisation moving population and the
farm share) are no longer a test: see Complaints 513 and 640."""
QUICK_TOPIC = True

import json
import os
import unittest
from types import SimpleNamespace

from sim.constants import REGISTRY
from sim.diffusion.literacy_rules import common_ceiling
from sim.labour.labour import Labour
from sim.tests.harness import NODES
from sim.tests.labour_stand_in import stand_in_world
from sim.world import agriculture, agriculture_labour, farming_technique

_REPOSITORY_SIM_DIRECTORY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MECHANISATION_NODES = ("horse_collar", "fud_heavy_mouldboard_plough_coulter", "fud_mechanical_reaper", "ag2_reaper")
CROP_NODES = ("mat_newworld_crops",)
DECLARATIONS = {node_id: node["mechanics"]["farming_technique"] for node_id, node in NODES.items()
                if "farming_technique" in (node.get("mechanics") or {})}


def _technique(node_ids):
    """The technique a society holding `node_ids`, all fully spread, farms with."""
    return farming_technique.technique_from_adoption({node_id: 1.0 for node_id in node_ids}, DECLARATIONS)


def _labour(done=(), year=100, done_year=None):
    world = stand_in_world()
    world.knowledge.nodes_with_mechanic = lambda mechanic: list(DECLARATIONS) if mechanic == "farming_technique" else []
    world.knowledge.mechanic = lambda node_id, mechanic: DECLARATIONS[node_id]
    world.projects.done = set(done)
    world.projects.done_year = dict(done_year or {})
    world.projects.granted = set()
    world.game = SimpleNamespace(year=year)
    return Labour(world), world


class TechniqueTests(unittest.TestCase):
    def test_a_society_without_draught_animals_farms_with_the_hoe(self):
        labour, _world = _labour()
        self.assertEqual(labour.allocation.farming_technique().toolkit, agriculture.HAND_HOE)

    def test_the_draught_capability_gives_the_ard_the_reference_toolkit(self):
        labour, world = _labour(done=("cap_power_muscle",))
        world.scenario.civ["starting_techs"] = list(world.scenario.civ.get("starting_techs", ())) + ["cap_power_muscle"]
        self.assertEqual(labour.allocation.farming_technique().toolkit._replace(name=agriculture.DEFAULT_TOOLKIT.name), agriculture.DEFAULT_TOOLKIT)

    def test_the_hoe_costs_the_hours_the_hoe_recipe_does(self):
        # The production data's own two wheat entries, both built from data/world/farm_labour.json.
        with open(os.path.join(os.path.dirname(_REPOSITORY_SIM_DIRECTORY), "data", "production", "40_organics.json"), encoding="utf-8") as handle:
            materials = json.load(handle)["materials"]
        hoe_over_plough = materials["wheat_hoe_kg"]["labour_hours"]["farmer"] / materials["wheat_kg"]["labour_hours"]["farmer"]
        self.assertAlmostEqual(agriculture.HAND_HOE.labour_hours_multiplier, hoe_over_plough, places=6)

    def test_adoption_grows_with_age(self):
        labour, world = _labour(done=("fud_mechanical_reaper",), year=100, done_year={"fud_mechanical_reaper": 100})
        early = labour.allocation.farming_technique().toolkit.reaping_rate_multiplier
        world.game.year += 60
        late = labour.allocation.farming_technique().toolkit.reaping_rate_multiplier
        self.assertGreater(late, early)

    def test_a_technology_the_society_started_with_is_fully_spread(self):
        labour, world = _labour(done=("fud_mechanical_reaper",), year=100, done_year={"fud_mechanical_reaper": 100})
        world.scenario.civ["starting_techs"] = list(world.scenario.civ.get("starting_techs", ())) + ["fud_mechanical_reaper"]
        self.assertAlmostEqual(labour.allocation.farming_technique().toolkit.reaping_rate_multiplier,
                               _technique(("fud_mechanical_reaper",)).toolkit.reaping_rate_multiplier)

    def test_a_technology_not_held_does_nothing(self):
        labour, _world = _labour(done=())
        self.assertEqual(labour.allocation.farming_technique(), farming_technique.DEFAULT_TECHNIQUE._replace(toolkit=farming_technique.BASE_TOOLKIT))


class MechanisationTests(unittest.TestCase):
    def test_mechanisation_raises_the_hectares_one_worker_brings_in(self):
        default = _technique(())
        improved = _technique(MECHANISATION_NODES)
        self.assertGreater(agriculture_labour.hectares_cropped_per_farm_worker(improved.crop, improved.toolkit),
                           agriculture_labour.hectares_cropped_per_farm_worker(default.crop, default.toolkit))

    def test_mechanisation_lets_fewer_farm_workers_feed_the_same_people(self):
        default, improved = _technique(()), _technique(MECHANISATION_NODES)
        needed = lambda technique: agriculture_labour.farm_workers_fte_for_population(
            1.0e6, technique.crop, None, technique.rotation, technique.toolkit)
        self.assertLess(needed(improved), needed(default))

    def test_a_crop_with_more_calories_per_hectare_lets_fewer_workers_feed_the_same_people(self):
        default, improved = _technique(()), _technique(CROP_NODES)
        needed = lambda technique: agriculture_labour.farm_workers_fte_for_population(
            1.0e6, technique.crop, None, technique.rotation, technique.toolkit)
        self.assertLess(needed(improved), needed(default))

class LiteracyCostTests(unittest.TestCase):
    def _ceiling(self, farm_share):
        return common_ceiling(REGISTRY["UNABLE_TO_READ_SHARE"]["value"], REGISTRY["FARM_CHILDREN_KEPT_FROM_SCHOOL"]["value"], farm_share)

    def test_the_elite_ceiling_is_everyone_who_can_learn_to_read(self):
        self.assertGreater(1.0 - REGISTRY["UNABLE_TO_READ_SHARE"]["value"], 0.97)

    def test_literacy_can_pass_the_old_elite_ceiling_with_a_small_farm_share(self):
        self.assertGreater(self._ceiling(0.02), 0.97 - 0.05)

    def test_a_large_farm_share_lowers_attainable_literacy(self):
        self.assertLess(self._ceiling(0.7), self._ceiling(0.05))


if __name__ == "__main__":
    unittest.main()
