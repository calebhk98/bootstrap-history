"""Hauls between tiles: modes from data, built ways, rivers and seas, reach, and search speed."""
import json
import os
import shutil
import tempfile
import time
import unittest

from sim.geography import api, map_source, parameters, routes_graph, routes_modes, routes_search, tile_holdings, tile_lookup

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "geography_fixtures")
ROUTES_SMALL = os.path.join(FIXTURES, "routes_small")
MOD_OVERLAY = os.path.join(FIXTURES, "routes_mod", "data", "world", "geography")
MOD_ID = "test_routes_k9"
DATA_FOLDER = map_source.BASE_MAP_FOLDER
ROUTE_CATALOGUES = ("route_modes", "sea_lanes", "parameters")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ANCIENT_NODES = {"sea_square_sail", "lnd_mule_transport", "lnd_two_wheel_cart", "lnd_ox_transport"}

_scratch = []


def tearDownModule():
    for folder in _scratch:
        shutil.rmtree(folder, ignore_errors=True)
    _scratch.clear()


def _route_data_folder():
    """A map folder holding only the real route catalogues, to lay under the fixture tiles."""
    if not _scratch or not os.path.isdir(_scratch[0]):
        _scratch.clear()
        folder = tempfile.mkdtemp(prefix="routes_data_")
        with open(os.path.join(folder, "map.json"), "w", encoding="utf-8") as handle:
            handle.write('{"id": "routes_data"}')
        for name in ROUTE_CATALOGUES:
            shutil.copytree(os.path.join(DATA_FOLDER, name), os.path.join(folder, name))
        _scratch.append(folder)
    return _scratch[0]


def small_map(with_mod=False):
    folders = [(None, ROUTES_SMALL), (None, _route_data_folder())]
    if with_mod:
        folders.append((MOD_ID, MOD_OVERLAY))
    return map_source.merge_folders(folders)


def legs_of(result):
    return [(leg["from"], leg["to"], leg["mode"]) for leg in result["legs"]]


class SmallMapTests(unittest.TestCase):
    def setUp(self):
        self.world_map = small_map()

    def test_a_road_beats_the_track_between_neighbours_once_built(self):
        cart_modes = {"cart", "road"}
        track = routes_search.route(self.world_map, ["a1"], ["a2"], cart_modes)
        self.assertEqual([leg["mode"] for leg in track["legs"]], ["cart"])
        built = {routes_search.edge_key("a2", "a1"): {"road": True}}
        road = routes_search.route(self.world_map, ["a1"], ["a2"], cart_modes, improvements=built)
        self.assertEqual([leg["mode"] for leg in road["legs"]], ["road"])
        self.assertLess(road["cost_per_tonne"], track["cost_per_tonne"])
        self.assertLess(road["days"], track["days"])

    def test_costs_from_one_origin_match_the_route_to_each_tile(self):
        modes = {"foot", "cart", "sail"}
        prices = {"foot": 3.0, "cart": 1.0, "sail": 0.2}
        costs = routes_search.costs_from(self.world_map, ["a1"], modes, mode_costs=prices, handling_costs={})
        self.assertEqual(costs["a1"], 0.0)
        for tile_id, cost in costs.items():
            found = routes_search.route(self.world_map, ["a1"], [tile_id], modes, mode_costs=prices, handling_costs={})
            self.assertAlmostEqual(cost, found["cost_per_tonne"], msg=tile_id)
        unreachable = set(self.world_map.tiles) - set(costs)
        for tile_id in unreachable:
            self.assertIsNone(routes_search.route(self.world_map, ["a1"], [tile_id], modes, mode_costs=prices,
                                                  handling_costs={}))

    def test_no_route_by_rail_without_track(self):
        self.assertIsNone(routes_search.route(self.world_map, ["a1"], ["a2"], {"rail"}))
        built = {routes_search.edge_key("a1", "a2"): {"rail": True}}
        railway = routes_search.route(self.world_map, ["a1"], ["a2"], {"rail"}, improvements=built)
        self.assertEqual([leg["mode"] for leg in railway["legs"]], ["rail"])

    def test_sea_needs_coastal_ends(self):
        self.assertIsNotNone(routes_search.route(self.world_map, ["a1"], ["b1"], {"sail"}))
        self.assertIsNone(routes_search.route(self.world_map, ["a1"], ["a3"], {"sail"}))
        self.assertIsNone(routes_search.route(self.world_map, ["a2"], ["b1"], {"sail"}))
        mixed = routes_search.route(self.world_map, ["a2"], ["b1"], {"sail", "foot"})
        self.assertEqual([leg["mode"] for leg in mixed["legs"]], ["foot", "sail"])

    def test_a_river_runs_faster_and_cheaper_downstream(self):
        downstream = routes_search.route(self.world_map, ["a3"], ["a1"], {"river_boat"})
        upstream = routes_search.route(self.world_map, ["a1"], ["a3"], {"river_boat"})
        self.assertLess(downstream["days"], upstream["days"])
        self.assertLess(downstream["cost_per_tonne"], upstream["cost_per_tonne"])

    def test_changing_mode_costs_handling_time_and_money(self):
        free = routes_search.route(self.world_map, ["a1"], ["a3"], {"foot", "river_boat"},
                                   handling_costs={})
        costly = routes_search.route(self.world_map, ["a1"], ["a3"], {"foot", "river_boat"},
                                     handling_costs={"foot": 50.0, "river_boat": 50.0})
        self.assertGreater(costly["cost_per_tonne"], free["cost_per_tonne"])
        stops = routes_search.route(self.world_map, ["a1"], ["b3"], {"foot", "river_boat"})
        self.assertGreater(stops["days"], sum(leg["days"] for leg in stops["legs"]) - 1e-9)

    def test_caller_prices_replace_physical_cost(self):
        one = routes_search.route(self.world_map, ["a1"], ["a2"], {"foot"}, mode_costs={"foot": 1.0}, handling_costs={})
        two = routes_search.route(self.world_map, ["a1"], ["a2"], {"foot"}, mode_costs={"foot": 2.0}, handling_costs={})
        self.assertAlmostEqual(two["cost_per_tonne"], 2.0 * one["cost_per_tonne"])
        self.assertGreater(one["cost_per_tonne"], one["km"] * 0.5)

    def test_a_modded_mode_unlocks_from_its_modded_node(self):
        world_map = small_map(with_mod=True)
        mode_id = MOD_ID + ":hovercart"
        self.assertNotIn(mode_id, routes_modes.usable_modes(world_map, [{"lnd_two_wheel_cart"}]))
        both = routes_modes.usable_modes(world_map, [{MOD_ID + ":hover_node"}, {MOD_ID + ":hover_node", "x"}])
        self.assertIn(mode_id, both)
        self.assertIn("foot", both)
        result = routes_search.route(world_map, ["a1"], ["a3"], {mode_id})
        self.assertEqual({leg["mode"] for leg in result["legs"]}, {mode_id})
        self.assertEqual(routes_modes.invalid_entries(world_map), [])

    def test_links_offer_the_economy_graph_shape(self):
        links = routes_graph.links(self.world_map, ["pack", "sail"])
        pack = [link for link in links if link[2] == "pack" and (link[0], link[1]) == ("a1", "a2")]
        self.assertEqual(len(pack), 1)
        self.assertGreater(pack[0][3], 400)
        self.assertTrue(any(link[2] == "sail" and {link[0], link[1]} == {"a1", "b1"} for link in links))
        self.assertFalse(any(link[2] == "sail" and "a2" in link[:2] for link in links))


class EarthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world_map = map_source.load_map()
        cls.italy = sorted(tile for tile in cls.world_map.tiles if tile.startswith("italy_"))
        cls.egypt = sorted(tile for tile in cls.world_map.tiles if tile.startswith("egypt_"))
        cls.luoyang = tile_lookup.nearest_tile_id(cls.world_map.tiles, 34.6, 112.4)

    def test_every_mode_and_parameter_is_documented(self):
        self.assertEqual(routes_modes.invalid_entries(self.world_map), [])
        self.assertEqual(parameters.invalid_entries(self.world_map), [])

    def test_italy_reaches_egypt_by_sea(self):
        result = routes_search.route(self.world_map, self.italy, self.egypt, {"sail"})
        self.assertIsNotNone(result)
        self.assertEqual({leg["mode"] for leg in result["legs"]}, {"sail"})
        self.assertGreater(result["days"], 5)

    def test_a_long_coastal_haul_prefers_sea_over_land(self):
        land_only = routes_search.route(self.world_map, ["italy_03"], ["egypt_08"], {"foot", "pack", "cart"})
        everything = routes_search.route(self.world_map, ["italy_03"], ["egypt_08"],
                                         {"foot", "pack", "cart", "sail", "river_boat"})
        sea_km = sum(leg["km"] for leg in everything["legs"] if leg["mode"] == "sail")
        self.assertGreater(sea_km, 0.8 * everything["km"])
        if land_only is not None:
            self.assertLess(everything["cost_per_tonne"] * 5, land_only["cost_per_tonne"])

    def test_walking_crosses_a_continent_with_no_tech(self):
        modes = routes_modes.usable_modes(self.world_map, [set()])
        self.assertEqual(modes, frozenset({"foot"}))
        result = routes_search.route(self.world_map, self.italy, [self.luoyang], modes)
        self.assertIsNotNone(result)
        self.assertGreater(result["km"], 6000)

    def test_reach_grows_with_better_modes(self):
        origin = ["italy_03"]
        foot = routes_search.reach(self.world_map, origin, {"foot"}, 60)
        pack = routes_search.reach(self.world_map, origin, {"foot", "pack", "cart"}, 60)
        sail = routes_search.reach(self.world_map, origin, {"foot", "pack", "cart", "sail"}, 60)
        self.assertLess(len(foot), len(pack))
        self.assertLess(len(pack), len(sail))
        self.assertTrue(set(foot) <= set(pack) <= set(sail))
        self.assertEqual(foot["italy_03"], 0.0)

    def test_open_sea_lanes_need_their_nodes(self):
        edge = next(edge for edge in routes_graph.graph(self.world_map).edges if edge.lane_nodes)
        pair = (edge.tile_a, edge.tile_b)
        without = routes_search.route(self.world_map, [pair[0]], [pair[1]], {"sail"})
        held = routes_search.route(self.world_map, [pair[0]], [pair[1]], {"sail"},
                                   held_nodes=edge.lane_nodes)
        self.assertIsNotNone(held)
        self.assertTrue(without is None or without["cost_per_tonne"] > held["cost_per_tonne"])

    def test_steamships_and_railways_need_their_nodes(self):
        held = routes_modes.usable_modes(self.world_map, [ANCIENT_NODES])
        self.assertTrue({"sail", "cart", "pack", "river_boat", "foot"} <= held)
        self.assertFalse({"rail", "steam_ship"} & held)

    def test_a_search_over_every_tile_is_quick(self):
        modes = set(routes_modes.modes(self.world_map))
        routes_search.route(self.world_map, ["italy_03"], [self.luoyang], modes)  # builds the graph
        started = time.time()
        reached = routes_search.reach(self.world_map, ["spain_03"], modes, 1.0e6,
                                      improvements={"x|y": {"road": True}})
        self.assertLess(time.time() - started, 0.5)
        self.assertGreater(len(reached), len(self.world_map.tiles) // 2)


if __name__ == "__main__":
    unittest.main()


class EarthSeaLinkTests(unittest.TestCase):
    """Sea edges come from the water-path catalogue, not chords between coastal tiles."""

    @classmethod
    def setUpClass(cls):
        cls.world_map = map_source.load_map()
        graph = routes_graph.graph(cls.world_map)
        cls.sea_neighbours = {}
        for edge in graph.edges:
            if edge.edge_class in ("coast", "open_sea"):
                cls.sea_neighbours.setdefault(edge.tile_a, set()).add(edge.tile_b)
                cls.sea_neighbours.setdefault(edge.tile_b, set()).add(edge.tile_a)

    def _tile_near(self, latitude, longitude):
        return tile_lookup.nearest_tile_id(self.world_map.tiles, latitude, longitude)

    def _civilisation(self, name):
        with open(os.path.join(ROOT, "data", "civilizations", name + ".json"), encoding="utf-8") as handle:
            return json.load(handle)

    def test_suez_is_not_a_canal(self):
        self.assertNotIn("saudi_arabia_10", self.sea_neighbours["egypt_08"])
        by_sail = routes_search.route(self.world_map, ["egypt_08"], ["saudi_arabia_10"], {"sail"})
        self.assertIsNone(by_sail)
        round_africa = routes_search.route(self.world_map, ["egypt_08"], ["saudi_arabia_10"], {"sail"},
                                           held_nodes={"exp_africa_circumnavigation", "exp_coastal_africa"})
        self.assertIsNotNone(round_africa)

    def test_a_landlocked_looking_tile_is_not_a_port(self):
        self.assertEqual(self.world_map.layers["is_port"]["values"]["laos_01"], 0)
        self.assertNotIn("laos_01", self.sea_neighbours)

    def test_the_bosporus_is_open_and_panama_is_closed(self):
        black_sea, aegean = self._tile_near(45.3, 33.0), self._tile_near(36.8, 30.5)
        self.assertIsNotNone(routes_search.route(self.world_map, [black_sea], [aegean], {"sail"}))
        caribbean, pacific = self._tile_near(22.0, -80.0), self._tile_near(-1.5, -80.5)
        everything = {"exp_africa_circumnavigation", "exp_coastal_africa", "exp_atlantic_crossing"}
        legs = routes_search.route(self.world_map, [caribbean], [pacific], {"sail"}, held_nodes=everything)["legs"]
        self.assertNotIn("panama_01", {tile for leg in legs for tile in (leg["from"], leg["to"])})

    def test_england_reaches_han_by_land_across_the_suez_isthmus(self):
        england, han = self._civilisation("england_1300"), self._civilisation("han_china_100ad")
        modes = api.usable_modes([england["starting_techs"], han["starting_techs"]])
        result = api.route(tile_holdings.tiles_held(england),
                           tile_holdings.tiles_held(han), modes,
                           held_nodes=set(england["starting_techs"]) | set(han["starting_techs"]))
        land_legs = [leg for leg in result["legs"] if leg["mode"] in ("pack", "cart", "foot")]
        self.assertTrue(land_legs)
        self.assertTrue(any(leg["from"].startswith("egypt_") or leg["to"].startswith("egypt_") for leg in land_legs))
