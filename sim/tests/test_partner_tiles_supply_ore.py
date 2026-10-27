"""A partner economy whose tiles hold a catalogue deposit worked by the start year has a supplying tile for that
ore: the firms' ore sites are not limited to the seat's own tiles. Without it a partner's bloom buyers have no
bloomery at home and its iron has to come from the seat's side of the map."""
QUICK_TOPIC = True

import unittest

from sim.markets import port_sites
from sim.engine.data import load_civ
from sim.geography import api as geography
from sim.tests.test_mine_names_a_deposit import _Host

PARTNER = "han_china_100ad"


class PartnerOreSiteTests(unittest.TestCase):

    def setUp(self):
        self.host = _Host()
        self.partner_tiles = geography.tiles_held(load_civ(PARTNER), self.host.world_map)
        self.ore_of = {ore: resource for resource, by_ore in geography.ore_goods(self.host.world_map).items()
                       for ore in by_ore}
        self.outputs = {ore: {ore: 1000.0} for ore in self.ore_of}
        self.limits = port_sites.site_limits(self.host, self.outputs, self.partner_tiles)

    def test_every_ore_with_a_sized_deposit_on_a_partner_tile_has_a_supplying_tile_there(self):
        year = self.host.state.scenario.year
        checked = 0
        for ore, resource in sorted(self.ore_of.items()):
            sized = {row["tile_id"] for row in geography.worked_deposits(self.partner_tiles, resource, year, (),
                                                                          self.host.world_map)
                     if row["size_tonnes"]}
            supplied = {limit.tile for limit in self.limits if limit.recipe_id == ore and limit.capacity_runs_per_year > 0.0}
            self.assertLessEqual(sized & set(self.partner_tiles), supplied | (sized - set(self.partner_tiles)), ore)
            checked += len(sized)
        self.assertGreater(checked, 0)

    def test_iron_ore_is_supplied_from_a_partner_tile(self):
        tiles = {limit.tile for limit in self.limits if limit.recipe_id == "iron_ore_kg" and limit.capacity_runs_per_year > 0.0}
        self.assertTrue(tiles & set(self.partner_tiles))

    def test_the_seat_cannot_name_a_partner_deposit(self):
        partner_rows = self.host.partner_deposits("iron", self.partner_tiles)
        self.assertTrue(partner_rows)
        found = {row["id"] for row in self.host.found_deposits("iron")}
        self.assertFalse(found & {row["id"] for row in partner_rows})

    def test_what_firms_raise_on_a_partner_tile_is_drawn_from_its_deposit(self):
        row = self.host.partner_deposits("iron", self.partner_tiles)[0]
        port_sites.deplete(self.host, {("iron_ore_kg", row["tile_id"]): 10.0}, self.outputs)
        self.assertGreater(self.host.holdings.deposit_drawn.get(row["id"], 0.0), 0.0)


if __name__ == "__main__":
    unittest.main()
