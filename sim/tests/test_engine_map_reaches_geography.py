"""Complaints 409 and 410, as wiring on stand-in selves: the engine's map is the base map opened with the installed mods
in load order (`GeographyPortMixin.world_map`), and the foreign haul asks geography about that map (`_foreign_route`
resolves the partner's tiles on it, `_haul_route` searches and reads modes on it). Collaborators are recorders; no game."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.engine import foreign_routes, geography_port
from sim.engine.foreign_routes import ForeignRoutesMixin

MAP = object()


class WorldMapTests(unittest.TestCase):
    def read(self, standin):
        manifests = [types.SimpleNamespace(id="first", directory="/mods/first"),
                     types.SimpleNamespace(id="second", directory="/mods/second")]
        with mock.patch.object(geography_port, "get_ordered_mods", return_value=manifests) as ordered, \
                mock.patch.object(geography_port, "open_map", return_value=MAP) as opened:
            return geography_port.GeographyPortMixin.world_map.fget(standin), ordered, opened

    def test_the_map_is_opened_with_each_installed_mod_in_load_order(self):
        world_map, ordered, opened = self.read(types.SimpleNamespace())
        self.assertIs(world_map, MAP)
        ordered.assert_called_once_with(geography_port.MODS_DIR)
        opened.assert_called_once_with([("first", "/mods/first"), ("second", "/mods/second")])

    def test_a_map_already_opened_is_kept(self):
        kept = object()
        standin = types.SimpleNamespace(_world_map=kept)
        _world_map, _ordered, opened = self.read(standin)
        opened.assert_not_called()
        self.assertIs(geography_port.GeographyPortMixin.world_map.fget(standin), kept)


class HaulRouteTests(unittest.TestCase):
    def standin(self):
        return types.SimpleNamespace(
            world_map=MAP, civ={"id": "home"}, held_and_running=lambda include_starting=True: frozenset({"home_tech"}),
            _freight_mode_costs=lambda imbalance: {"cart": 1.0},
            _freight_handling_costs=lambda: {}, _with_carried_provisions=lambda route, rates, searched: route,
            _share_delivered_on=lambda mode, route: 1.0)

    def haul(self):
        found = object()
        asked = {}

        def choose(search, cost, mode_costs, share):
            return search(mode_costs)

        with mock.patch.object(foreign_routes, "tiles_held", return_value=["home_tile"]) as held, \
                mock.patch.object(foreign_routes, "usable_route_modes", return_value=["cart"]) as modes, \
                mock.patch.object(foreign_routes, "route_over_tiles", return_value=found) as searched, \
                mock.patch.object(foreign_routes, "route_from_geography", side_effect=lambda route: route), \
                mock.patch.object(foreign_routes.foreign_route_choice, "choose_route", side_effect=choose):
            ForeignRoutesMixin._haul_route(self.standin(), ["origin_tile"], 0.0, "goods", frozenset({"foreign_tech"}))
        asked.update(held=held, modes=modes, searched=searched)
        return asked

    def test_this_societys_tiles_are_resolved_on_the_engine_map(self):
        self.haul()["held"].assert_called_once_with({"id": "home"}, MAP)

    def test_the_usable_modes_are_read_from_the_engine_map(self):
        self.assertEqual(self.haul()["modes"].call_args.args[1], MAP)

    def test_the_route_is_searched_on_the_engine_map_between_the_given_and_held_tiles(self):
        call = self.haul()["searched"].call_args
        self.assertIs(call.kwargs["world_map"], MAP)
        self.assertEqual(call.args[0], ["origin_tile"])
        self.assertEqual(call.args[1], ["home_tile"])


class ForeignRouteTests(unittest.TestCase):
    def test_the_partners_tiles_are_resolved_on_the_engine_map_and_hauled(self):
        hauled = []
        standin = types.SimpleNamespace(
            world_map=MAP, nodes={}, _foreign_flow_imbalance=lambda civilization_id: 0.25,
            _haul_route=lambda *arguments: hauled.append(arguments) or "route")
        partner = {"id": "partner", "starting_techs": ["a"]}
        with mock.patch.object(foreign_routes, "tiles_held", return_value=["partner_tile"]) as held, \
                mock.patch.object(foreign_routes.action_results, "expand", return_value=frozenset({"a"})):
            route = ForeignRoutesMixin._foreign_route(standin, partner)
        held.assert_called_once_with(partner, MAP)
        self.assertEqual(route, "route")
        self.assertEqual(hauled, [(["partner_tile"], 0.25, "goods", frozenset({"a"}))])


if __name__ == "__main__":
    unittest.main()
