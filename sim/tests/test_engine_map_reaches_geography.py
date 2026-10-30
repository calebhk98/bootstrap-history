"""Complaints 409 and 410, as wiring on stand-in selves: the engine's map is the base map opened with the installed mods
in load order (`Land.world_map`), and the foreign haul asks the land module about it (the freight module's `foreign_route`
asks which tiles the partner's file lists, `haul_route` asks the usable modes and searches). Collaborators are recorders;
no game."""
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

        def tiles_listed_by(civilisation):
            asked["held"] = civilisation
            return ["home_tile"]

        def modes_usable(parties, cargo="goods"):
            asked["modes"] = (tuple(parties), cargo)
            return ["cart"]

        def cheapest_route(*arguments, **keywords):
            asked["searched"] = (arguments, keywords)
            return found

        def choose(search, cost, mode_costs, share):
            return search(mode_costs)

        module = module_harness.build(_Searched, views={
            "tiles_listed_by": tiles_listed_by, "modes_usable": modes_usable, "cheapest_route": cheapest_route,
            "civilisation": lambda: {"id": "home"}, "held_techniques": lambda include_starting: frozenset({"home_tech"})})
        with mock.patch.object(routes, "route_from_geography", side_effect=lambda route: route), \
                mock.patch.object(routes, "choose_route", side_effect=choose):
            module.haul_route(["origin_tile"], 0.0, "goods", frozenset({"foreign_tech"}))
        return asked

    def test_this_societys_tiles_are_the_ones_the_land_module_lists_for_its_civilisation(self):
        self.assertEqual(self.haul()["held"], {"id": "home"})

    def test_the_usable_modes_are_asked_for_the_techniques_of_both_parties(self):
        self.assertEqual(self.haul()["modes"], ((frozenset({"home_tech"}), frozenset({"foreign_tech"})), "goods"))

    def test_the_route_is_searched_between_the_given_and_held_tiles_over_the_usable_modes(self):
        arguments, keywords = self.haul()["searched"]
        self.assertEqual(arguments[:3], (["origin_tile"], ["home_tile"], ["cart"]))
        self.assertEqual(keywords["held_nodes"], frozenset({"home_tech", "foreign_tech"}))


class ForeignRouteTests(unittest.TestCase):
    def test_the_partners_tiles_are_listed_by_the_land_module_and_hauled(self):
        hauled, listed = [], []

        class Hauled(Freight):
            def foreign_flow_imbalance(self, civilization_id):
                return 0.25

            def haul_route(self, *arguments):
                hauled.append(arguments)
                return "route"
        module = module_harness.build(Hauled, views={
            "tiles_listed_by": lambda civilisation: listed.append(civilisation) or ["partner_tile"],
            "techniques_with_results": lambda techniques: frozenset({"a"})})
        partner = {"id": "partner", "starting_techs": ["a"]}
        route = module.foreign_route(partner)
        self.assertEqual(listed, [partner])
        self.assertEqual(route, "route")
        self.assertEqual(hauled, [(["partner_tile"], 0.25, "goods", frozenset({"a"}))])


if __name__ == "__main__":
    unittest.main()
