"""Complaints/416 (415): the agent economy's ore firms work the deposits the seat has found, tile by tile, and
what they raise is drawn from those deposits."""
QUICK_TOPIC = True

import unittest

from sim.engine import economy_port_sites
from sim.geography import api as geography
from sim.tests.test_mine_names_a_deposit import _Host

ORE = "iron_ore_kg"
OUTPUTS = {ORE: {ORE: 1000.0}, "coal_kg": {"coal_kg": 1000.0}, "bread_kg": {"bread_kg": 5.0}}


class SiteLimitTests(unittest.TestCase):

    def setUp(self):
        self.host = _Host()
        self.limits = economy_port_sites.site_limits(self.host, OUTPUTS)

    def test_only_ore_recipes_are_sited_and_each_tile_holds_a_limit_from_its_deposits(self):
        self.assertTrue(self.limits)
        self.assertEqual({limit.recipe_id for limit in self.limits}, {ORE})
        rows = self.host.found_deposits("iron")
        for limit in self.limits:
            ore_kg = sum(row["room_tonnes_per_year"] * geography.ore_tonnes_per_tonne(row) * 1000.0
                         for row in rows if row["tile_id"] == limit.tile)
            self.assertAlmostEqual(limit.capacity_runs_per_year * 1000.0, ore_kg)

    def test_room_the_seats_own_mines_took_is_not_given_to_firms(self):
        row = self.host.found_deposits("iron")[0]
        before = {limit.tile: limit.capacity_runs_per_year for limit in self.limits}[row["tile_id"]]
        self.host.open_mine("iron", row["room_tonnes_per_year"], deposit=row["id"])
        after = {limit.tile: limit.capacity_runs_per_year
                 for limit in economy_port_sites.site_limits(self.host, OUTPUTS)}[row["tile_id"]]
        self.assertLess(after, before)

    def test_a_tile_whose_deposit_is_worked_out_keeps_a_limit_of_nothing(self):
        for row in self.host.found_deposits("iron"):
            self.host.draw_deposit(row["id"], row["size_tonnes"])
        limits = economy_port_sites.site_limits(self.host, OUTPUTS)
        self.assertTrue(limits)
        self.assertEqual({limit.capacity_runs_per_year for limit in limits}, {0.0})


class DepletionTests(unittest.TestCase):

    def test_what_firms_raise_on_a_tile_is_drawn_from_its_deposits(self):
        host = _Host()
        row = max(host.found_deposits("iron"), key=lambda found: found["remaining_tonnes"])
        runs = 50.0
        economy_port_sites.deplete(host, {(ORE, row["tile_id"]): runs}, OUTPUTS)
        ore_tonnes = runs * 1000.0 / 1000.0
        drawn = sum(host.state.holdings.deposit_drawn.values())
        self.assertAlmostEqual(drawn * geography.ore_tonnes_per_tonne(row), ore_tonnes)

    def test_nothing_is_drawn_for_a_recipe_that_is_not_ore_or_a_tile_with_no_deposit(self):
        host = _Host()
        economy_port_sites.deplete(host, {("bread_kg", "anywhere"): 10.0, (ORE, "no_such_tile"): 10.0}, OUTPUTS)
        self.assertEqual(host.state.holdings.deposit_drawn, {})


if __name__ == "__main__":
    unittest.main()
