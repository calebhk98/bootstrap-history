"""Complaints/416: what a road or railway costs to build comes from the terrain it crosses."""
import unittest

from sim.geography import api, routes_graph


def _land_edges():
    world_map = api.open_map()
    return world_map, [edge for edge in routes_graph.graph(world_map).edges if edge.edge_class == "land"]


class WaysBuildTests(unittest.TestCase):

    def test_a_road_costs_labour_and_stone_and_a_railway_adds_rails(self):
        world_map, edges = _land_edges()
        edge = next(edge for edge in edges if edge.grade <= 0.05)
        road = api.build_requirements(edge.tile_a, edge.tile_b, "road", world_map=world_map)
        rail = api.build_requirements(edge.tile_a, edge.tile_b, "rail", world_map=world_map)
        self.assertGreater(road["labour_hours"], 0.0)
        self.assertGreater(road["materials"]["stone_kg"], 0.0)
        self.assertNotIn("iron", road["materials"])
        self.assertGreater(rail["materials"]["iron"], 0.0)

    def test_steeper_ground_costs_more_labour_per_km(self):
        world_map, edges = _land_edges()
        buildable = [edge for edge in edges
                     if api.build_requirements(edge.tile_a, edge.tile_b, "road", world_map=world_map)]
        flat, steep = min(buildable, key=lambda edge: edge.grade), max(buildable, key=lambda edge: edge.grade)
        self.assertGreater(steep.grade, flat.grade)

        def per_km(edge):
            found = api.build_requirements(edge.tile_a, edge.tile_b, "road", world_map=world_map)
            return found["labour_hours"] / found["km"]
        self.assertGreater(per_km(steep), per_km(flat))

    def test_ground_steeper_than_the_engineered_limit_cannot_be_built(self):
        world_map, edges = _land_edges()
        limit = world_map.catalogue("route_modes")["rail"]["engineered"]["max_grade"]
        too_steep = max(edges, key=lambda edge: edge.grade)
        found = api.build_requirements(too_steep.tile_a, too_steep.tile_b, "rail", world_map=world_map)
        self.assertEqual(found is None, too_steep.grade > limit)

    def test_tiles_that_do_not_border_have_no_way(self):
        world_map, edges = _land_edges()
        self.assertIsNone(api.build_requirements(edges[0].tile_a, "no_such_tile", "road", world_map=world_map))

    def test_a_built_road_makes_the_edge_usable_by_the_road_mode(self):
        world_map, edges = _land_edges()
        edge = next(edge for edge in edges if edge.grade <= 0.05)
        held = {"lnd_two_wheel_cart"}
        modes = api.usable_modes([held])
        built = {api.edge_key(edge.tile_a, edge.tile_b): {"road": True}}
        plain = api.route([edge.tile_a], [edge.tile_b], modes, world_map=world_map, held_nodes=held)
        paved = api.route([edge.tile_a], [edge.tile_b], modes, improvements=built, world_map=world_map,
                          held_nodes=held)
        self.assertTrue(any(leg["mode"] == "road" for leg in paved["legs"]))
        self.assertLessEqual(paved["cost_per_tonne"], plain["cost_per_tonne"])

    def test_built_length_counts_only_the_named_way_over_the_edges_it_covers(self):
        world_map, edges = _land_edges()
        first, second = [edge for edge in edges if edge.grade <= 0.05][:2]
        built = {api.edge_key(first.tile_a, first.tile_b): {"road": True, "rail": True},
                 api.edge_key(second.tile_a, second.tile_b): {"road": True}}
        road_km = api.built_km(built, "road", world_map=world_map)
        rail_km = api.built_km(built, "rail", world_map=world_map)
        self.assertEqual(api.built_km({}, "road", world_map=world_map), 0.0)
        self.assertGreater(road_km, rail_km)
        self.assertGreater(rail_km, 0.0)


if __name__ == "__main__":
    unittest.main()
