"""Complaints/416: the engine keeps the roads and track an actor has built, pays labour and material
for them from the terrain, and routes over them.

Geography's own rules (what a way costs, which edges can be built, that a built road beats a track) are in
test_geography_ways_build.py and test_geography_routes.py; here the saved state is a round trip of built state, and
the engine's wiring to the labour market, the purse, the routes and the command are named scenarios."""
import random
import unittest

from sim import simulator
from sim.engine.core import Sim
from sim.engine.state import deserialize_state, serialize_state, EconomyState
from sim.geography import api as geography

_TREE, _PRICES, _NODES, _WAGES, _GOODS = simulator.load()


def _fresh_sim(civ="rome_100ad"):
    return Sim(_NODES, list(_NODES), random.Random(1), civ=simulator.load_civ(civ))


def _buildable_pair(sim, way="road"):
    """Two bordering held tiles a way can be built between."""
    held = set(sim.labour.settlement_tiles())
    for tile in sorted(held):
        for other in sorted(geography.tile_facts(tile, sim.world_map)["neighbours"]):
            if other in held and geography.build_requirements(tile, other, way, sim.world_map):
                return tile, other
    raise AssertionError("no buildable pair")


def _finish_building(sim):
    """Move the calendar to the year the last way under construction opens, and open it."""
    due_years = [build["due"] for ways in sim.state.economy.ways_under_construction.values() for build in ways.values()]
    if due_years:
        sim.state.scenario.year = max(due_years)
    sim.finish_ways()


class BuiltWaysTests(unittest.TestCase):

    def test_scenario_building_a_road_records_it_charges_labour_and_stone_and_is_what_routes_use(self):
        sim = _fresh_sim()
        tile_a, tile_b = _buildable_pair(sim)
        sim.state.household.capital = 1e12
        quote = sim.way_quote(tile_a, tile_b, "road")
        self.assertGreater(quote["money"], 0.0)
        before = sim.state.household.capital
        ok, message = sim.build_way(tile_a, tile_b, "road")
        self.assertTrue(ok, message)
        self.assertNotIn(geography.edge_key(tile_a, tile_b), sim.state.economy.improvements)
        _finish_building(sim)
        self.assertTrue(sim.state.economy.improvements[geography.edge_key(tile_a, tile_b)]["road"])
        # a balance near 1e12 carries rounding far coarser than 1e-4, so compare by share of the quote
        self.assertAlmostEqual(before - sim.state.household.capital, quote["money"], delta=1e-9 * quote["money"])
        self.assertIn(geography.edge_key(tile_a, tile_b), sim.ways_built())

    def test_scenario_building_is_refused_without_the_money_the_technology_or_a_border(self):
        sim = _fresh_sim()
        tile_a, tile_b = _buildable_pair(sim)
        sim.state.household.capital = 0.0
        self.assertFalse(sim.build_way(tile_a, tile_b, "road")[0])
        sim.state.household.capital = 1e12
        self.assertFalse(sim.build_way(tile_a, "no_such_tile", "road")[0])
        self.assertFalse(sim.build_way(tile_a, tile_b, "rail")[0])
        self.assertEqual(sim.state.economy.improvements, {})

    def test_the_built_and_building_ways_survive_save_and_load(self):
        economy = EconomyState()
        economy.improvements = {"a|b": {"road": True, "canal": True}}
        economy.ways_under_construction = {"b|c": {"road": {"due": 130, "crew_trade": "labourer", "hours_a_year": 4000.0,
                                                          "engineered": False, "pressed": 128}}}
        copy = deserialize_state(serialize_state(economy), EconomyState)
        self.assertEqual(copy.improvements, economy.improvements)
        self.assertEqual(copy.ways_under_construction, economy.ways_under_construction)

    def test_scenario_roads_along_the_cheapest_route_lower_its_cost_and_never_slow_the_household(self):
        sim = _fresh_sim()
        sim.state.household.capital = 1e12
        base = sim.labour.base_tile()
        far = max((tile for tile in sim.labour.settlement_tiles() if tile != base),
                  key=lambda tile: sim.labour.distance_to_tile_km(tile))
        held = sim.labour.held_technologies()
        modes = geography.usable_modes([held])
        route = geography.route([base], [far], modes, held_nodes=held)
        days_before = sim.labour.travel_days_to_tile(far)
        for leg in route["legs"]:
            sim.build_way(leg["from"], leg["to"], "road")
        _finish_building(sim)
        self.assertTrue(sim.state.economy.improvements)
        built = geography.route([base], [far], modes, sim.ways_built(), held_nodes=held)
        self.assertLess(built["cost_per_tonne"], route["cost_per_tonne"])
        self.assertLessEqual(sim.labour.travel_days_to_tile(far), days_before + 1e-9)

    def test_scenario_a_way_takes_its_crew_from_the_labour_market_until_it_opens(self):
        sim = _fresh_sim()
        tile_a, tile_b = _buildable_pair(sim)
        sim.state.household.capital = 1e12
        market = sim.labour.labour_market
        before = market.pressure("labourer")
        ok, message = sim.build_way(tile_a, tile_b, "road")
        self.assertTrue(ok, message)
        self.assertGreater(market.pressure("labourer"), before)
        pressed = market.pressure("labourer")
        _finish_building(sim)
        self.assertLess(market.pressure("labourer"), pressed)

    def test_scenario_the_command_previews_and_builds(self):
        from sim.ui.proto.dispatch import _agent_dispatch
        from sim.ui.proto.typed import parse_typed
        sim = _fresh_sim()
        sim.state.household.capital = 1e12
        tile_a, tile_b = _buildable_pair(sim)
        command, error = parse_typed("build_way road %s %s preview" % (tile_a, tile_b))
        self.assertIsNone(error)
        preview = _agent_dispatch(sim, _NODES, command)
        self.assertTrue(preview["ok"] and preview["preview"], preview)
        self.assertEqual(sim.state.economy.improvements, {})
        command["preview"] = False
        self.assertTrue(_agent_dispatch(sim, _NODES, command)["ok"])
        _finish_building(sim)
        self.assertIn(geography.edge_key(tile_a, tile_b), sim.ways_built())


if __name__ == "__main__":
    unittest.main()
