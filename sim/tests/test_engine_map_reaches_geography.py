"""Complaints 409 and 410, as wiring on stand-in selves: the engine's map is the base map opened with the installed mods
in load order (`Land.world_map`), and the foreign haul asks geography about that map (the freight module's
`foreign_route` resolves the partner's tiles on it, `haul_route` searches and reads modes on it). Collaborators are
recorders; no game."""
QUICK_TOPIC = True

import unittest
from unittest import mock

from sim.land import map_views
from sim.land.module import Land
from sim.freight import routes
from sim.freight.module import Freight
from sim.tests import module_harness

MAP = object()


class WorldMapTests(unittest.TestCase):
    def read(self, overlays):
        module = module_harness.build(Land, views={"map_overlays": lambda: overlays})
        with mock.patch.object(map_views, "open_map", return_value=MAP) as opened:
            return module.world_map, module, opened

    def test_the_map_is_opened_with_each_installed_mod_in_load_order(self):
        world_map, _module, opened = self.read([("first", "/mods/first"), ("second", "/mods/second")])
        self.assertIs(world_map, MAP)
        opened.assert_called_once_with([("first", "/mods/first"), ("second", "/mods/second")])

    def test_a_map_already_opened_is_kept(self):
        _world_map, module, opened = self.read([])
        opened.reset_mock()
        with mock.patch.object(map_views, "open_map", return_value=object()) as reopened:
            self.assertIs(module.world_map, MAP)
        reopened.assert_not_called()
        opened.assert_not_called()


class _Searched(Freight):
    """The freight module with its mode costs and provisions written out."""

    def freight_mode_costs(self, imbalance=1.0, modes=None, cargo=None):
        return {"cart": 1.0}

    def freight_handling_costs(self):
        return {}

    def with_carried_provisions(self, route, base_rates=None, searched_rates=None):
        return route

    def share_delivered_on(self, mode, route):
        return 1.0


class HaulRouteTests(unittest.TestCase):
    def haul(self):
        found = object()
        asked = {}

        def choose(search, cost, mode_costs, share):
            return search(mode_costs)

        module = module_harness.build(_Searched, views={
            "legacy_world_map": lambda: MAP, "civilisation": lambda: {"id": "home"},
            "held_techniques": lambda include_starting: frozenset({"home_tech"})})
        with mock.patch.object(routes, "tiles_held", return_value=["home_tile"]) as held, \
                mock.patch.object(routes, "usable_route_modes", return_value=["cart"]) as modes, \
                mock.patch.object(routes, "route_over_tiles", return_value=found) as searched, \
                mock.patch.object(routes, "route_from_geography", side_effect=lambda route: route), \
                mock.patch.object(routes, "choose_route", side_effect=choose):
            module.haul_route(["origin_tile"], 0.0, "goods", frozenset({"foreign_tech"}))
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

        class Hauled(Freight):
            def foreign_flow_imbalance(self, civilization_id):
                return 0.25

            def haul_route(self, *arguments):
                hauled.append(arguments)
                return "route"
        module = module_harness.build(Hauled, views={
            "legacy_world_map": lambda: MAP, "techniques_with_results": lambda techniques: frozenset({"a"})})
        partner = {"id": "partner", "starting_techs": ["a"]}
        with mock.patch.object(routes, "tiles_held", return_value=["partner_tile"]) as held:
            route = module.foreign_route(partner)
        held.assert_called_once_with(partner, MAP)
        self.assertEqual(route, "route")
        self.assertEqual(hauled, [(["partner_tile"], 0.25, "goods", frozenset({"a"}))])


if __name__ == "__main__":
    unittest.main()
