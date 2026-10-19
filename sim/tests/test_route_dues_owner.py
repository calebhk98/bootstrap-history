"""Complaint 599: a route's dues belong to the holder of the tile where they are levied, are charged per tonne
carried and are paid into that holder's treasury; a change of holder moves the revenue."""

import unittest

from sim.engine.haul_route import Leg, Route
from sim.geography import api as geography_api


def _legs(*stops):
    """Legs [(origin tile, mode)] as the route search states them."""
    return [{"from": tile, "mode": mode} for tile, mode in stops]


class DuesByHolder(unittest.TestCase):

    def test_each_due_goes_to_the_holder_of_the_tile_it_is_levied_at(self):
        owners = {"a": "rome", "b": "carthage"}
        levied = geography_api.route_dues_levied(
            _legs(("a", "river_boat"), ("b", "sail")), {"river_boat": 2.0, "sail": 3.0}, owners.get)
        self.assertEqual([(due["tile"], due["holder"], due["per_tonne"]) for due in levied],
                         [("a", "rome", 2.0), ("b", "carthage", 3.0)])

    def test_dues_scale_with_the_tonnes_carried(self):
        owners = {"a": "rome"}
        once = geography_api.route_dues_by_holder(_legs(("a", "sail")), {"sail": 3.0}, owners.get, tonnes=10.0)
        twice = geography_api.route_dues_by_holder(_legs(("a", "sail")), {"sail": 3.0}, owners.get, tonnes=20.0)
        self.assertAlmostEqual(twice["rome"], 2.0 * once["rome"])

    def test_dues_are_levied_once_where_the_haul_changes_to_a_mode_not_on_each_hop(self):
        owners = {"a": "rome", "b": "carthage", "c": "rome"}
        levied = geography_api.route_dues_levied(
            _legs(("a", "sail"), ("b", "sail"), ("c", "foot"), ("a", "sail")), {"sail": 3.0}, owners.get)
        self.assertEqual([(due["tile"], due["holder"]) for due in levied], [("a", "rome"), ("a", "rome")])

    def test_a_mode_with_no_dues_and_an_unheld_tile_levy_nothing(self):
        self.assertEqual(geography_api.route_dues_levied(
            _legs(("a", "foot"), ("zz", "sail")), {"sail": 3.0}, {"a": "rome"}.get), [])


class DuesSettled(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from . import harness
        cls.game = harness.unopened_sim()
        cls.tiles = sorted(cls.game.tile_owner_map())
        cls.route = Route((Leg(cls.tiles[0], cls.tiles[1], "river_boat", 10.0, 1.0),
                           Leg(cls.tiles[1], cls.tiles[2], "sail", 50.0, 1.0)))

    def _revenue(self, holder, tonnes):
        treasury = self.game.route_dues_treasury(holder)
        before = treasury.money
        paid = self.game.pay_route_dues(self.game.household, self.route, tonnes)
        return paid, treasury.money - before

    def test_dues_go_to_the_holders_treasury_and_scale_with_tonnes(self):
        holder = self.game.civ["id"]
        for tile in self.tiles[:2]:
            self.game.transfer_tile(tile, holder, cause="test")
        paid_ten, gained_ten = self._revenue(holder, 10.0)
        paid_twenty, gained_twenty = self._revenue(holder, 20.0)
        self.assertGreater(gained_ten, 0.0)
        self.assertAlmostEqual(paid_ten, gained_ten)
        self.assertAlmostEqual(paid_twenty, 2.0 * paid_ten)
        self.assertAlmostEqual(gained_twenty, 2.0 * gained_ten)

    def test_a_change_of_holder_moves_the_revenue(self):
        first, second = self.game.civ["id"], "second_holder"
        for tile in self.tiles[:2]:
            self.game.transfer_tile(tile, first, cause="test")
        _paid, first_gain = self._revenue(first, 10.0)
        for tile in self.tiles[:2]:
            self.game.transfer_tile(tile, second, cause="test")
        first_treasury = self.game.route_dues_treasury(first)
        first_before = first_treasury.money
        _paid, second_gain = self._revenue(second, 10.0)
        self.assertAlmostEqual(second_gain, first_gain)
        self.assertEqual(first_treasury.money, first_before)


class DuesOnATraderCargo(unittest.TestCase):

    def test_a_partner_route_pays_its_dues_to_the_holder_of_each_tile_and_never_more_than_the_freight(self):
        from . import harness
        from sim.engine.agents_port import SimWorld
        game = harness.unopened_sim()
        world = SimWorld(game)
        partner = "han_china_100ad"
        facts = game._foreign_economy_facts(partner)
        route = facts["route"]
        if route is None:
            self.skipTest("no route joins the partner")
        paid = {}
        for tonnes in (10.0, 20.0):
            paid[tonnes] = world.pay_route_dues(game.household, world._home_place(), partner, "grain", tonnes)
        freight = world.freight_between(world._home_place(), partner, "grain", 10.0)
        self.assertLessEqual(paid[10.0], freight + 1e-9)
        self.assertAlmostEqual(paid[20.0], 2.0 * paid[10.0])


if __name__ == "__main__":
    unittest.main()
