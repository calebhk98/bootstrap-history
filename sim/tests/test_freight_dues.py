"""Complaints/326: tolls and port dues are mode data the route search charges per leg, labelled with a source or as a heuristic."""
import unittest

from sim.geography import api as geography_api
from sim.geography.api import dues_hours_per_tonne


class FreightDues(unittest.TestCase):

    def test_foreign_routes_charge_the_dues_in_wages(self):
        from . import harness
        game = harness.sim(agent_economy=False)
        wage = game.labour.wage_per_hour(game.FREIGHT_DRIVER_WAGE_TRADE)
        charges = game._freight_handling_costs()
        dues = dues_hours_per_tonne()
        self.assertAlmostEqual(charges["river_boat"], dues["river_boat"] * wage)
        self.assertGreater(charges["sail"], dues["sail"] * wage)    # port handling comes on top
        self.assertNotIn("foot", charges)

    def test_water_and_port_modes_state_dues_and_foot_porters_none(self):
        dues = dues_hours_per_tonne()
        for mode in ("river_boat", "sail", "steam_ship"):
            self.assertGreater(dues[mode], 0.0, mode)
        self.assertEqual(dues["foot"], 0.0)

    def test_every_nonzero_due_names_its_basis(self):
        entries = geography_api.open_map().catalogue("route_modes")
        for mode, hours in dues_hours_per_tonne().items():
            if hours > 0.0:
                self.assertTrue(entries[mode].get("dues_source"), mode)
                self.assertIn(entries[mode].get("dues_conf"), ("A", "B", "C", "D"), mode)

    def test_dues_raise_a_route_that_changes_to_the_mode(self):
        tiles = geography_api.tile_ids()
        coastal = [tile for tile in tiles if geography_api.tile_facts(tile).get("coastal")]
        held = {"sea_square_sail"}
        origin = coastal[0]
        reached = geography_api.route_costs([origin], ["sail"], mode_costs={"sail": 1.0}, held_nodes=held)
        destination = max((tile for tile in reached if tile != origin), key=reached.get)
        plain = geography_api.route([origin], [destination], ["sail"], mode_costs={"sail": 1.0},
                                    handling_costs={"sail": 0.0}, held_nodes=held)
        charged = geography_api.route([origin], [destination], ["sail"], mode_costs={"sail": 1.0},
                                      handling_costs={"sail": 7.0}, held_nodes=held)
        self.assertIsNotNone(plain)
        self.assertAlmostEqual(charged["cost_per_tonne"] - plain["cost_per_tonne"], 7.0, places=6)


if __name__ == "__main__":
    unittest.main()
