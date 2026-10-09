"""Complaints/416: bridges over river crossings, ports on a coast tile, canals as a built water way, and
engineered ways over ground steeper than the natural limit, all priced from construction data and read
by the route search."""
QUICK_TOPIC = True

import unittest

from sim.geography import api, routes_graph, tile_layers

HELD = {"lnd_two_wheel_cart", "lnd_ox_transport", "lnd_steam_locomotive"}


def _edges(world_map, edge_class="land"):
    return [edge for edge in routes_graph.graph(world_map).edges if edge.edge_class == edge_class]


def _river_crossing(world_map, grade_limit):
    return next(edge for edge in _edges(world_map) if edge.crosses_river and edge.grade <= grade_limit)


def _dry_edge(world_map, grade_limit):
    return next(edge for edge in _edges(world_map) if not edge.crosses_river and edge.grade <= grade_limit)


def _unlisted_port(world_map):
    """A coastal tile with no natural harbour, bordering one that has."""
    for tile_id, tile in sorted(world_map.tiles.items()):
        if tile.get("coastal") and not tile_layers.value(world_map, tile_id, "is_port") and any(
                tile_layers.value(world_map, other, "is_port") for other in tile["borders"] if other in world_map.tiles):
            return tile_id
    raise AssertionError("no coastal tile without a harbour")


class EngineeredWaysTests(unittest.TestCase):

    def setUp(self):
        self.world_map = api.open_map()

    def test_a_railway_over_ground_steeper_than_the_natural_limit_is_engineered_at_more_earthwork(self):
        steep = next(edge for edge in _edges(self.world_map) if 0.08 < edge.grade <= 0.2)
        flat = _dry_edge(self.world_map, 0.03)
        found = api.build_requirements(steep.tile_a, steep.tile_b, "rail", world_map=self.world_map)
        level = api.build_requirements(flat.tile_a, flat.tile_b, "rail", world_map=self.world_map)
        self.assertTrue(found["engineered"])
        self.assertFalse(level["engineered"])
        self.assertGreater(found["labour_hours"] / found["km"], level["labour_hours"] / level["km"])

    def test_ground_beyond_the_engineered_limit_cannot_be_built(self):
        mountain = max(_edges(self.world_map), key=lambda edge: edge.grade)
        engineered_limit = self.world_map.catalogue("route_modes")["rail"]["engineered"]["max_grade"]
        if mountain.grade > engineered_limit:
            self.assertIsNone(api.build_requirements(mountain.tile_a, mountain.tile_b, "rail", world_map=self.world_map))
        else:
            self.assertIsNotNone(api.build_requirements(mountain.tile_a, mountain.tile_b, "rail", world_map=self.world_map))

    def test_an_engineered_edge_routes_only_once_the_way_is_marked_engineered(self):
        steep = next(edge for edge in _edges(self.world_map) if 0.08 < edge.grade <= 0.2 and not edge.crosses_river)
        key = api.edge_key(steep.tile_a, steep.tile_b)
        plain = api.route([steep.tile_a], [steep.tile_b], {"rail"}, improvements={key: {"rail": True}},
                          world_map=self.world_map, held_nodes=HELD)
        engineered = api.route([steep.tile_a], [steep.tile_b], {"rail"},
                               improvements={key: {"rail": True, "engineered": True}},
                               world_map=self.world_map, held_nodes=HELD)
        self.assertIsNone(plain)
        self.assertIsNotNone(engineered)


class BridgeTests(unittest.TestCase):

    def setUp(self):
        self.world_map = api.open_map()

    def test_a_bridge_is_priced_over_a_river_crossing_and_nowhere_else(self):
        crossing = _river_crossing(self.world_map, 0.1)
        dry = _dry_edge(self.world_map, 0.1)
        found = api.build_requirements(crossing.tile_a, crossing.tile_b, "bridge", world_map=self.world_map)
        self.assertGreater(found["labour_hours"], 0.0)
        self.assertGreater(found["materials"]["stone_kg"], 0.0)
        self.assertGreater(found["build_years"], 0.0)
        self.assertIsNone(api.build_requirements(dry.tile_a, dry.tile_b, "bridge", world_map=self.world_map))

    def test_an_unbridged_crossing_costs_a_cart_its_handling_and_a_bridge_removes_it(self):
        crossing = _river_crossing(self.world_map, 0.05)
        key = api.edge_key(crossing.tile_a, crossing.tile_b)
        args = ([crossing.tile_a], [crossing.tile_b], {"cart"})
        forded = api.route(*args, world_map=self.world_map, held_nodes=HELD, handling_costs={})
        bridged = api.route(*args, improvements={key: {"bridge": True}}, world_map=self.world_map,
                            held_nodes=HELD, handling_costs={})
        self.assertGreater(forded["days"], bridged["days"])

    def test_a_railway_cannot_ford_a_river(self):
        crossing = _river_crossing(self.world_map, 0.03)
        key = api.edge_key(crossing.tile_a, crossing.tile_b)
        args = ([crossing.tile_a], [crossing.tile_b], {"rail"})
        self.assertIsNone(api.route(*args, improvements={key: {"rail": True}}, world_map=self.world_map, held_nodes=HELD))
        self.assertIsNotNone(api.route(*args, improvements={key: {"rail": True, "bridge": True}},
                                       world_map=self.world_map, held_nodes=HELD))

    def test_built_bridges_are_counted_in_kilometres_of_span(self):
        crossing = _river_crossing(self.world_map, 0.1)
        key = api.edge_key(crossing.tile_a, crossing.tile_b)
        self.assertGreater(api.built_km({key: {"bridge": True}}, "bridge", world_map=self.world_map), 0.0)
        self.assertEqual(api.built_km({}, "bridge", world_map=self.world_map), 0.0)


class PortTests(unittest.TestCase):

    def setUp(self):
        self.world_map = api.open_map()
        self.tile = _unlisted_port(self.world_map)
        self.harbour = next(other for other in self.world_map.tiles[self.tile]["borders"]
                            if tile_layers.value(self.world_map, other, "is_port"))

    def test_a_port_is_priced_on_a_coast_tile_without_a_harbour_only(self):
        found = api.build_requirements(self.tile, self.tile, "port", world_map=self.world_map)
        self.assertGreater(found["materials"]["stone_kg"], 0.0)
        self.assertIsNone(api.build_requirements(self.harbour, self.harbour, "port", world_map=self.world_map))

    def test_a_built_port_opens_the_tile_to_sea_modes(self):
        sea_held = {"sea_square_sail"}
        far = next(edge.tile_b for edge in _edges(self.world_map, "coast") if edge.tile_a == self.harbour)
        built = {self.tile: {"port": True}}
        self.assertIsNone(api.route([self.tile], [far], {"sail"}, world_map=self.world_map, held_nodes=sea_held))
        self.assertIsNotNone(api.route([self.tile], [far], {"sail"}, improvements=built,
                                       world_map=self.world_map, held_nodes=sea_held))

    def test_the_improvement_key_of_a_port_is_its_tile(self):
        self.assertEqual(api.improvement_key("port", self.tile, self.tile, self.world_map), self.tile)
        self.assertEqual(api.improvement_key("road", "b", "a", self.world_map), api.edge_key("a", "b"))


class DataTests(unittest.TestCase):

    def test_the_works_catalogue_is_complete_and_the_map_has_no_problems(self):
        world_map = api.open_map()
        self.assertEqual(api.problems(world_map), [])
        self.assertEqual({"bridge", "port"}, set(world_map.catalogue("ways")))


class CanalTests(unittest.TestCase):

    def setUp(self):
        self.world_map = api.open_map()

    def test_a_canal_is_a_built_water_way_barges_use(self):
        flat = _dry_edge(self.world_map, 0.02)
        found = api.build_requirements(flat.tile_a, flat.tile_b, "canal", world_map=self.world_map)
        road = api.build_requirements(flat.tile_a, flat.tile_b, "road", world_map=self.world_map)
        self.assertGreater(found["labour_hours"], road["labour_hours"])
        key = api.edge_key(flat.tile_a, flat.tile_b)
        args = ([flat.tile_a], [flat.tile_b], {"canal"})
        self.assertIsNone(api.route(*args, world_map=self.world_map, held_nodes=HELD))
        routed = api.route(*args, improvements={key: {"canal": True}}, world_map=self.world_map, held_nodes=HELD)
        self.assertEqual([leg["mode"] for leg in routed["legs"]], ["canal"])


if __name__ == "__main__":
    unittest.main()
