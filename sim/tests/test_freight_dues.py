"""Complaints/326: tolls and port dues are mode data the route search charges per leg, labelled with a source or as a heuristic."""

QUICK_TOPIC = True

import unittest

from sim.engine.route_dues import dues_money_per_tonne, handling_money_per_tonne
from sim.geography import api as geography_api
from sim.geography.api import dues_hours_per_tonne


class FreightDues(unittest.TestCase):

    def test_dues_are_charged_in_wages_and_port_handling_comes_on_top(self):
        dues = {"river_boat": 2.0, "sail": 3.0, "foot": 0.0}
        charges = handling_money_per_tonne(dues, wage=5.0, port_mode="sail", port_handling_hours=1.5)
        self.assertAlmostEqual(charges["river_boat"], 10.0)
        self.assertAlmostEqual(charges["sail"], 3.0 * 5.0 + 1.5 * 5.0)
        self.assertNotIn("foot", charges)

    def test_port_handling_is_charged_even_where_the_port_mode_levies_no_dues(self):
        charges = handling_money_per_tonne({"sail": 0.0}, wage=4.0, port_mode="sail", port_handling_hours=2.0)
        self.assertAlmostEqual(charges["sail"], 8.0)

    def test_dues_alone_leave_out_modes_without_dues(self):
        self.assertEqual(dues_money_per_tonne({"river_boat": 2.0, "foot": 0.0}, wage=3.0), {"river_boat": 6.0})

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
