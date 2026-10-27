"""Complaints/416: a way's crew is hired through the labour market for the build years, and the engine
builds bridges, ports, canals and engineered ways; the roads, bridges and ports are recorded under the keys
geography's routes read."""
QUICK_TOPIC = True

from sim.finance import purchase_rules
import types
import unittest

from sim.engine import ways
from sim.geography import api as geography, routes_graph, tile_layers

GRANTED = {"civ_road_paved", "lnd_iron_edge_rail", "lnd_bridge", "civ_harbour_dock", "civ_canal_pound_lock"}


class _LabourMarket:
    """A market with a fixed number of labourers to be found, recording what is pressed and released."""

    def __init__(self, supply):
        self.supply = supply
        self.pressed = []
        self.released = []

    def quote(self, trade, hours=0.0, employer=None, pay_premium=0.0):
        return 2.0

    def whole_recruits(self, trade, people, pay_premium=0.0):
        return int(min(people, max(1, self.supply)))

    def hire(self, employer, trade, hours, pay_premium=0.0):
        self.pressed.append((trade, hours))
        return 2.0

    def press(self, trade, hours):
        self.pressed.append((trade, hours))

    def release(self, employer, trade, hours):
        self.released.append((trade, hours))


class _Builder(ways.WaysMixin):
    """The parts of a Sim that building a way touches."""

    def __init__(self, held, supply=100000):
        self.world_map = geography.open_map()
        self.state = types.SimpleNamespace(
            economy=types.SimpleNamespace(improvements={}, ways_under_construction={}),
            scenario=types.SimpleNamespace(year=100),
            projects=types.SimpleNamespace(done=set(), granted=set(GRANTED)),
            household=object())
        self.market = _LabourMarket(supply)
        self.labour = types.SimpleNamespace(labour_market=self.market, settlement_tiles=lambda: sorted(held))
        self.goods_market = types.SimpleNamespace(purchase_cost=lambda material, tonnes: (10.0 * tonnes, 10.0))
        self.paid = []

    def spending_power(self, kind):
        return 1e18

    def view(self, name):
        """The finance module's `can_pay` over this stand-in's spending power."""
        return lambda cost: purchase_rules.can_pay(cost, self.spending_power("buy"))

    def pay_edge(self, edge, money, text):
        self.paid.append(money)

    def finish_works(self):
        pass


def _land_edges(world_map):
    return [edge for edge in routes_graph.graph(world_map).edges if edge.edge_class == "land"]


def _builder_for(edge, supply=100000):
    return _Builder({edge.tile_a, edge.tile_b}, supply)


def _flat(world_map):
    return next(edge for edge in _land_edges(world_map) if edge.grade < 0.03 and not edge.crosses_river)


def _open(builder, years_on=0.0):
    builder.state.scenario.year += years_on
    builder.finish_ways()


class CrewFromTheLabourMarketTests(unittest.TestCase):

    def setUp(self):
        self.world_map = geography.open_map()
        self.edge = _flat(self.world_map)

    def test_the_build_takes_as_long_as_the_crew_the_market_finds_can_work(self):
        plenty = _builder_for(self.edge)
        scarce = _builder_for(self.edge, supply=20)
        years_plenty = plenty.way_quote(self.edge.tile_a, self.edge.tile_b, "road")["years"]
        years_scarce = scarce.way_quote(self.edge.tile_a, self.edge.tile_b, "road")["years"]
        self.assertGreater(years_scarce, 10.0 * years_plenty)

    def test_starting_a_way_leans_on_the_crews_trade_and_finishing_it_gives_the_hands_back(self):
        builder = _builder_for(self.edge)
        ok, message = builder.build_way(self.edge.tile_a, self.edge.tile_b, "road")
        self.assertTrue(ok, message)
        self.assertEqual([trade for trade, _hours in builder.market.pressed], ["labourer"])
        crew_hours = builder.market.pressed[0][1]
        self.assertGreater(crew_hours, 0.0)
        due = next(iter(next(iter(builder.state.economy.ways_under_construction.values())).values()))["due"]
        self.assertEqual(builder.market.released, [])
        _open(builder, due - builder.state.scenario.year)
        self.assertEqual(builder.market.released, [("labourer", crew_hours)])

    def test_each_year_of_the_build_presses_the_market_again(self):
        builder = _builder_for(self.edge, supply=30)
        builder.build_way(self.edge.tile_a, self.edge.tile_b, "road")
        before = len(builder.market.pressed)
        _open(builder, 1.0)
        _open(builder, 1.0)
        self.assertEqual(len(builder.market.pressed), before + 2)
        _open(builder, 0.0)
        self.assertEqual(len(builder.market.pressed), before + 2)


class EngineeredAndWorksTests(unittest.TestCase):

    def setUp(self):
        self.world_map = geography.open_map()

    def _finish(self, builder):
        builder.state.scenario.year = 10 ** 6
        builder.finish_ways()

    def test_a_railway_over_steep_ground_is_built_engineered_and_recorded_so(self):
        edge = next(edge for edge in _land_edges(self.world_map) if 0.08 < edge.grade <= 0.2 and not edge.crosses_river)
        builder = _builder_for(edge)
        self.assertTrue(builder.way_quote(edge.tile_a, edge.tile_b, "rail")["engineered"])
        self.assertTrue(builder.build_way(edge.tile_a, edge.tile_b, "rail")[0])
        self._finish(builder)
        built = builder.state.economy.improvements[geography.edge_key(edge.tile_a, edge.tile_b)]
        self.assertTrue(built["rail"] and built["engineered"])

    def test_a_level_road_is_not_engineered(self):
        edge = _flat(self.world_map)
        builder = _builder_for(edge)
        builder.build_way(edge.tile_a, edge.tile_b, "road")
        self._finish(builder)
        self.assertNotIn("engineered", builder.state.economy.improvements[geography.edge_key(edge.tile_a, edge.tile_b)])

    def test_a_bridge_is_recorded_on_the_crossing_edge(self):
        edge = next(edge for edge in _land_edges(self.world_map) if edge.crosses_river)
        builder = _builder_for(edge)
        self.assertTrue(builder.build_way(edge.tile_a, edge.tile_b, "bridge")[0])
        self._finish(builder)
        self.assertTrue(builder.state.economy.improvements[geography.edge_key(edge.tile_a, edge.tile_b)]["bridge"])

    def test_a_bridge_is_refused_where_no_river_is_crossed(self):
        edge = _flat(self.world_map)
        self.assertFalse(_builder_for(edge).build_way(edge.tile_a, edge.tile_b, "bridge")[0])

    def test_a_port_is_recorded_under_its_tile_and_needs_the_tile_held(self):
        tile = next(tile_id for tile_id, tile in sorted(self.world_map.tiles.items())
                    if tile.get("coastal") and not tile_layers.value(self.world_map, tile_id, "is_port"))
        builder = _Builder({tile})
        self.assertTrue(builder.build_way(tile, tile, "port")[0])
        self._finish(builder)
        self.assertTrue(builder.state.economy.improvements[tile]["port"])
        self.assertFalse(_Builder(set()).build_way(tile, tile, "port")[0])

    def test_a_canal_is_built_like_any_other_way(self):
        edge = _flat(self.world_map)
        builder = _builder_for(edge)
        self.assertTrue(builder.build_way(edge.tile_a, edge.tile_b, "canal")[0])
        self._finish(builder)
        self.assertTrue(builder.state.economy.improvements[geography.edge_key(edge.tile_a, edge.tile_b)]["canal"])


class CommandAndSaveTests(unittest.TestCase):

    def test_the_typed_command_names_a_port_by_one_tile(self):
        from sim.ui.proto.typed import parse_typed
        command, error = parse_typed("build_way port some_tile preview")
        self.assertIsNone(error)
        self.assertEqual((command["way"], command["from"], command["to"]), ("port", "some_tile", "some_tile"))
        command, error = parse_typed("build_way road tile_a tile_b")
        self.assertEqual((command["from"], command["to"]), ("tile_a", "tile_b"))

    def test_a_way_under_construction_survives_save_and_load(self):
        from sim.engine.state import EconomyState, deserialize_state, serialize_state
        economy = EconomyState()
        economy.ways_under_construction = {"a|b": {"rail": {"due": 12.5, "trade": "labourer", "crew_hours": 3.0e5,
                                                           "engineered": True, "pressed": 3}}}
        economy.improvements = {"a|b": {"road": True, "engineered": True}, "tile": {"port": True}}
        copy = deserialize_state(serialize_state(economy), EconomyState)
        self.assertEqual(copy.ways_under_construction, economy.ways_under_construction)
        self.assertEqual(copy.improvements, economy.improvements)


class BuiltWaysAndCommandTests(unittest.TestCase):
    """What the engine keeps of built ways is what geography's routes take, and the build_way command calls the
    engine's quote and build."""

    def test_ways_built_is_the_improvements_record_geographys_routes_take(self):
        record = {"a|b": {"road": True}}
        game = types.SimpleNamespace(state=types.SimpleNamespace(economy=types.SimpleNamespace(improvements=record)))
        self.assertIs(ways.WaysMixin.ways_built(game), record)

    def _command(self, **keywords):
        return dict({"cmd": "build_way", "way": "road", "from": "a", "to": "b"}, **keywords)

    def test_a_preview_quotes_without_building(self):
        from sim.ui.proto.dispatch_ways import _cmd_build_way
        built = []
        quote = {"km": 12.34, "labour_hours": 1000.4, "materials": {"stone": 55.5}, "money": 999.9, "years": 2.26,
                 "engineered": False}
        game = types.SimpleNamespace(way_quote=lambda a, b, way: quote, build_way=lambda a, b, way: built.append(way))
        reply = _cmd_build_way(game, {}, self._command(preview=True), None)
        self.assertEqual((reply["ok"], reply["preview"], reply["km"], reply["labour_hours"], reply["materials_tonnes"],
                          reply["money"], reply["years"]), (True, True, 12.3, 1000, {"stone": 56}, 1000, 2.3))
        self.assertEqual(built, [])

    def test_a_preview_of_a_way_that_cannot_be_built_is_refused_with_the_cause(self):
        from sim.ui.proto.dispatch_ways import _cmd_build_way
        from sim.refusal import Refusal
        game = types.SimpleNamespace(way_quote=lambda a, b, way: None,
                                     way_refusal=lambda a, b, way: Refusal("no_river", "no river to bridge"))
        reply = _cmd_build_way(game, {}, self._command(way="bridge", preview=True), None)
        self.assertEqual((reply["ok"], reply["cause"]), (False, "no_river"))

    def test_a_build_command_builds_the_named_way_between_the_named_tiles(self):
        from sim.ui.proto.dispatch_ways import _cmd_build_way
        calls = []
        game = types.SimpleNamespace(way_quote=lambda a, b, way: {}, capital=123.45,
                                     build_way=lambda a, b, way: (calls.append((a, b, way)) or (True, "started")))
        reply = _cmd_build_way(game, {}, self._command(), None)
        self.assertEqual(calls, [("a", "b", "road")])
        self.assertEqual((reply["ok"], reply["built"], reply["capital"]), (True, "started", 123.5))


if __name__ == "__main__":
    unittest.main()
