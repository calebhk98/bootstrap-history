"""Complaints 57 and 58: the cohort model is the only population, and a civilisation's farming technique reaches yield, labour and
literacy through the labour market rather than through side scalars.

The technique is read by `Labour` over a stand-in world (the tree's own farming declarations), and the food, labour and
literacy rules are called as functions; no game is built. The decades-long runs (food and mechanisation moving population and the
farm share) are test_population_farm_technique_scenario."""
QUICK_TOPIC = True

import os
import unittest
from types import SimpleNamespace

from sim.constants import REGISTRY
from sim.engine.literacy_rules import common_ceiling
from sim.labour import labour_allocation
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
    world.nodes_with_mechanic = lambda mechanic: list(DECLARATIONS) if mechanic == "farming_technique" else []
    world.mechanic = lambda node_id, mechanic: DECLARATIONS[node_id]
    world.state.projects.done = set(done)
    world.state.projects.done_year = dict(done_year or {})
    world.state.projects.granted = set()
    world.state.scenario = SimpleNamespace(year=year)
    return Labour(world), world


class NoSecondPopulationTests(unittest.TestCase):
    def _offenders(self, banned):
        offenders = []
        for directory, _, files in os.walk(_REPOSITORY_SIM_DIRECTORY):
            for name in files:
                path = os.path.join(directory, name)
                if not name.endswith(".py") or path == os.path.abspath(__file__):
                    continue
                with open(path, encoding="utf-8") as handle:
                    text = handle.read()
                offenders += [(path, word) for word in banned if word in text]
        return offenders

    def test_no_population_scale_scalar_anywhere(self):
        self.assertEqual(self._offenders(("_pop_scale" + "_base", "_pop_tech" + "_pending")), [])

    def test_no_mechanisation_count_gates_literacy(self):
        self.assertEqual(self._offenders(("agrarian" + "_slack",)), [])


class TechniqueTests(unittest.TestCase):
    def test_default_technique_is_the_reference_one(self):
        labour, _world = _labour()
        self.assertEqual(labour._farming_technique().toolkit, agriculture.DEFAULT_TOOLKIT)

    def test_adoption_grows_with_age(self):
        labour, world = _labour(done=("fud_mechanical_reaper",), year=100, done_year={"fud_mechanical_reaper": 100})
        early = labour._farming_technique().toolkit.reaping_rate_multiplier
        world.state.scenario.year += 60
        late = labour._farming_technique().toolkit.reaping_rate_multiplier
        self.assertGreater(late, early)

    def test_a_technology_the_society_started_with_is_fully_spread(self):
        labour, world = _labour(done=("fud_mechanical_reaper",), year=100, done_year={"fud_mechanical_reaper": 100})
        world.civ["starting_techs"] = list(world.civ.get("starting_techs", ())) + ["fud_mechanical_reaper"]
        self.assertAlmostEqual(labour._farming_technique().toolkit.reaping_rate_multiplier,
                               _technique(("fud_mechanical_reaper",)).toolkit.reaping_rate_multiplier)

    def test_a_technology_not_held_does_nothing(self):
        labour, _world = _labour(done=())
        self.assertEqual(labour._farming_technique(), farming_technique.DEFAULT_TECHNIQUE)


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

    def test_a_better_toolkit_lets_the_same_cleared_land_be_worked_by_fewer_hands(self):
        common = dict(baseline_fte=1.0e9, current_fte=1.0e9, shortfall_kg=0.0, marginal_product_kg_per_hour=5.0, land_hectares=1.0e5)
        default = labour_allocation.farm_workers_needed(technique=_technique(()), **common)
        improved = labour_allocation.farm_workers_needed(technique=_technique(MECHANISATION_NODES), **common)
        self.assertLess(improved, default)


class WorkersMoveOnlyAsFastAsTheMarketLetsThem(unittest.TestCase):
    TOTAL = 1.0e6

    def test_a_farm_that_needs_far_fewer_hours_sheds_some_but_not_all_in_a_year(self):
        after = labour_allocation.farm_hours_after(self.TOTAL * 0.8, self.TOTAL * 0.1, self.TOTAL)
        self.assertLess(after, self.TOTAL * 0.8)
        self.assertGreater(after, self.TOTAL * 0.1)
        self.assertGreater(after, 0.5 * self.TOTAL * 0.8)       # mobility bounds one year's move

    def test_a_farm_that_needs_more_hours_gains_some_but_not_all_in_a_year(self):
        after = labour_allocation.farm_hours_after(self.TOTAL * 0.1, self.TOTAL * 0.8, self.TOTAL)
        self.assertGreater(after, self.TOTAL * 0.1)
        self.assertLess(after, self.TOTAL * 0.8)

    def test_a_farm_that_needs_what_it_has_stays_put(self):
        self.assertAlmostEqual(labour_allocation.farm_hours_after(self.TOTAL * 0.5, self.TOTAL * 0.5, self.TOTAL), self.TOTAL * 0.5)

    def test_hours_stay_within_the_society_s_hours(self):
        self.assertLessEqual(labour_allocation.farm_hours_after(self.TOTAL * 0.99, self.TOTAL * 5.0, self.TOTAL), self.TOTAL)
        self.assertGreaterEqual(labour_allocation.farm_hours_after(0.0, -1.0, self.TOTAL), 0.0)


class LiteracyCostTests(unittest.TestCase):
    def _ceiling(self, farm_share):
        return common_ceiling(REGISTRY["UNABLE_TO_READ_SHARE"]["value"], REGISTRY["FARM_CHILDREN_KEPT_FROM_SCHOOL"]["value"], farm_share)

    def test_the_elite_ceiling_is_everyone_who_can_learn_to_read(self):
        self.assertGreater(1.0 - REGISTRY["UNABLE_TO_READ_SHARE"]["value"], 0.97)

    def test_literacy_can_pass_the_old_elite_ceiling_with_a_small_farm_share(self):
        self.assertGreater(self._ceiling(0.02), 0.97 - 0.05)

    def test_a_large_farm_share_lowers_attainable_literacy(self):
        self.assertLess(self._ceiling(0.7), self._ceiling(0.05))


class SurplusResponseTests(unittest.TestCase):
    def test_a_surplus_lowers_farm_need_and_a_shortfall_raises_it(self):
        common = dict(baseline_fte=100.0, current_fte=100.0, marginal_product_kg_per_hour=5.0, land_hectares=1e9)
        surplus = labour_allocation.farm_workers_needed(shortfall_kg=0.0, surplus_kg=1e6, **common)
        shortfall = labour_allocation.farm_workers_needed(shortfall_kg=1e6, surplus_kg=0.0, **common)
        self.assertLess(surplus, 100.0)
        self.assertGreater(shortfall, 100.0)
        self.assertGreaterEqual(surplus, 0.0)


if __name__ == "__main__":
    unittest.main()
