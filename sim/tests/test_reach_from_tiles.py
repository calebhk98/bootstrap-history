"""Complaints/416 and 136: a region's reach is the fewest days from the tiles a civilisation holds,
over the modes it holds and the ways it has built; no region id is special-cased and no region
carries a hand-set distance."""
import os
import random
import unittest

from sim import simulator
from sim.engine.core import Sim
from sim.geography import api as geography

_TREE, _PRICES, _NODES, _WAGES, _GOODS = simulator.load()
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _fresh_sim(civ):
    return Sim(_NODES, list(_NODES), random.Random(1), civ=simulator.load_civ(civ))


def _total_reach(sim):
    return sum(sim.geography.region_reach(region_id) for region_id in sim.geography.regions)


class ReachFromTilesTests(unittest.TestCase):

    def test_a_region_whose_tile_is_held_is_reach_zero_and_others_are_not(self):
        sim = _fresh_sim("rome_100ad")
        held_regions = {geography.tile_facts(tile, sim.world_map)["region"] for tile in geography.tiles_held(sim.civ)}
        for region_id in sim.geography.regions:
            if region_id in held_regions:
                self.assertEqual(sim.geography.region_reach(region_id), 0, region_id)
            else:
                self.assertGreaterEqual(sim.geography.region_reach(region_id), 1, region_id)

    def test_listing_tiles_instead_of_labels_moves_the_reach_with_them(self):
        sim = _fresh_sim("rome_100ad")
        far = geography.tiles_of_regions(["china"])[:1]
        sim.civ = dict(sim.civ, home_tiles=far)
        self.assertEqual(sim.geography.region_reach("china"), 0)
        self.assertGreater(sim.geography.region_reach("italia"), 0)

    def test_more_carriage_techniques_bring_places_nearer(self):
        sim = _fresh_sim("mexica_1500")
        before = _total_reach(sim)
        sim.state.projects.granted.update({"sea_square_sail", "lnd_two_wheel_cart", "lnd_mule_transport"})
        self.assertLess(_total_reach(sim), before)

    def test_a_region_no_route_joins_is_the_farthest_level(self):
        sim = _fresh_sim("mexica_1500")
        self.assertEqual(sim.geography.region_reach("italia"), max(int(level) for level in sim.geography.data["reach_levels"]))

    def test_no_region_record_carries_a_distance_or_a_reach(self):
        for region_id, record in _fresh_sim("rome_100ad").geography.regions.items():
            self.assertFalse({"reach_from_italia", "route_difficulty", "coastal", "reach"} & set(record), region_id)

    def test_a_located_material_costs_nothing_extra_where_the_tile_of_a_place_is_held(self):
        for civilisation in ("rome_100ad", "mexica_1500"):
            sim = _fresh_sim(civilisation)
            for node_id, material_key in sorted(sim.geography._mat_unlock.items()):
                held = any(sim.geography.tile_reach(tile_id) == 0
                           for tile_id in sim.geography._material_tiles[material_key])
                factor = sim.geography.material_cost_factor(node_id)
                if held:
                    self.assertEqual(factor, 1.0, (civilisation, node_id))
                else:
                    self.assertGreaterEqual(factor, 1.0, (civilisation, node_id))

    def test_no_engine_or_geography_code_names_a_region(self):
        offenders = []
        for folder in ("sim/engine", "sim/geography", "sim/labour", "sim/economy"):
            for name in sorted(os.listdir(os.path.join(_ROOT, folder))):
                if name.endswith(".py"):
                    with open(os.path.join(_ROOT, folder, name), encoding="utf-8") as handle:
                        text = handle.read()
                    if '"italia"' in text or "'italia'" in text:
                        offenders.append(folder + "/" + name)
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
