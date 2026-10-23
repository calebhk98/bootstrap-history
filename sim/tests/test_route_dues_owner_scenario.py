"""SCENARIO (Complaint 599): a route's dues are paid into the holder's treasury in a real game, scale with the tonnes, move with
a change of holder, and a trader's cargo pays them to the holder of each tile. The dues rule is in test_route_dues_owner."""

import unittest

from sim.engine.haul_route import Leg, Route


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
        self.assertIsNotNone(route, "no route joins the partner")
        paid = {}
        for tonnes in (10.0, 20.0):
            paid[tonnes] = world.pay_route_dues(game.household, world._home_place(), partner, "grain", tonnes)
        freight = world.freight_between(world._home_place(), partner, "grain", 10.0)
        self.assertLessEqual(paid[10.0], freight + 1e-9)
        self.assertAlmostEqual(paid[20.0], 2.0 * paid[10.0])


if __name__ == "__main__":
    unittest.main()
