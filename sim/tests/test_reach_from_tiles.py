"""Complaints/416 and 136: a region's reach is the fewest days from the tiles a civilisation holds,
over the modes it holds and the ways it has built.

Geography is opened on the real map and geography data with a small stand-in for the engine, so no game is built."""
QUICK_TOPIC = True

import json
import os
import unittest

from sim.geography import api as geography
from sim.geography import map_source
from sim.geography.geography import Geography
from sim.tests.ui_stand_in import FactViews

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class _World:
    """The parts of the engine that Geography reads."""

    pop_scale = 1.0

    def __init__(self, civilisation):
        self.civ = civilisation
        self.held_nodes = set(civilisation.get("starting_techs") or ())
        self.improvements = {}
        self.world_map = map_source.load_map()

    def civilisation(self, civilisation_id):
        return _civilisation(civilisation_id)


def _civilisation(civilisation_id):
    with open(os.path.join(_ROOT, "data", "civilizations", civilisation_id + ".json"), encoding="utf-8") as handle:
        return json.load(handle)


class _Sim(FactViews):
    """A civilisation's geography on the real map, with the civilisation and the nodes held open to change."""

    def __init__(self, civilisation_id):
        self.world = _World(_civilisation(civilisation_id))
        self.geography = Geography(self.world)
        self.geography.open(geography.load_geography())

    @property
    def civ(self):
        return self.world.civ

    @civ.setter
    def civ(self, value):
        self.world.civ = value

    @property
    def world_map(self):
        return self.world.world_map


def _fresh_sim(civ):
    return _Sim(civ)


def _total_reach(sim):
    return sum(sim.view("legacy_geography")().region_reach(region_id) for region_id in sim.view("legacy_geography")().regions)


class ReachFromTilesTests(unittest.TestCase):

    def test_a_region_whose_tile_is_held_is_reach_zero_and_others_are_not(self):
        sim = _fresh_sim("rome_100ad")
        held_regions = {geography.tile_facts(tile, sim.view("legacy_world_map")())["region"] for tile in geography.tiles_held(sim.civ)}
        for region_id in sim.view("legacy_geography")().regions:
            if region_id in held_regions:
                self.assertEqual(sim.view("legacy_geography")().region_reach(region_id), 0, region_id)
            else:
                self.assertGreaterEqual(sim.view("legacy_geography")().region_reach(region_id), 1, region_id)

    def test_listing_tiles_instead_of_labels_moves_the_reach_with_them(self):
        sim = _fresh_sim("rome_100ad")
        far = geography.tiles_of_regions(["china"])[:1]
        sim.civ = dict(sim.civ, home_tiles=far)
        self.assertEqual(sim.view("legacy_geography")().region_reach("china"), 0)
        self.assertGreater(sim.view("legacy_geography")().region_reach("italia"), 0)

    def test_more_carriage_techniques_bring_places_nearer(self):
        sim = _fresh_sim("mexica_1500")
        before = _total_reach(sim)
        sim.world.held_nodes.update({"sea_square_sail", "lnd_two_wheel_cart", "lnd_mule_transport"})
        self.assertLess(_total_reach(sim), before)

    def test_a_region_no_route_joins_is_the_farthest_level(self):
        sim = _fresh_sim("mexica_1500")
        self.assertEqual(sim.view("legacy_geography")().region_reach("italia"), max(int(level) for level in sim.view("legacy_geography")().data["reach_levels"]))

    def test_no_region_record_carries_a_distance_or_a_reach(self):
        for region_id, record in _fresh_sim("rome_100ad").view("legacy_geography")().regions.items():
            self.assertFalse({"reach_from_italia", "route_difficulty", "coastal", "reach"} & set(record), region_id)

    def test_a_located_material_costs_nothing_extra_where_the_tile_of_a_place_is_held(self):
        for civilisation in ("rome_100ad", "mexica_1500"):
            sim = _fresh_sim(civilisation)
            for node_id, material_key in sorted(sim.view("legacy_geography")()._mat_unlock.items()):
                held = any(sim.view("legacy_geography")().tile_reach(tile_id) == 0
                           for tile_id in sim.view("legacy_geography")()._material_tiles[material_key])
                factor = sim.view("legacy_geography")().material_cost_factor(node_id)
                if held:
                    self.assertEqual(factor, 1.0, (civilisation, node_id))
                else:
                    self.assertGreaterEqual(factor, 1.0, (civilisation, node_id))


if __name__ == "__main__":
    unittest.main()
