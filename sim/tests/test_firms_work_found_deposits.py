"""Complaints/416 (415): the agent economy's ore firms work the deposits the seat has found, tile by tile, and
what they raise is drawn from those deposits. The rules are called on a stand-in host holding written-out deposit rows;
the room the seat's own mines take is `found_deposits` (test_mine_names_a_deposit)."""
QUICK_TOPIC = True

import types
import unittest

from sim.engine import economy_port_sites
from sim.geography import api as geography

ORE = "iron_ore_kg"
OUTPUTS = {ORE: {ORE: 1000.0}, "coal_kg": {"coal_kg": 1000.0}, "bread_kg": {"bread_kg": 5.0}}
WORLD_MAP = geography.open_map()


def deposit(deposit_id, tile, room, remaining, grade=None):
    return {"id": deposit_id, "tile_id": tile, "room_tonnes_per_year": room, "remaining_tonnes": remaining,
            "grade_kg_per_tonne": grade}


class Host:
    """Holds the deposits the seat has found for iron, and records what is drawn from them."""
    def __init__(self, rows):
        self.rows, self.drawn = rows, []
        self.world_map = WORLD_MAP
        self.state = types.SimpleNamespace(economy=types.SimpleNamespace())

    def found_deposits(self, resource_id):
        return list(self.rows) if resource_id == "iron" else []

    def partner_deposits(self, resource_id, tile_ids):
        return []

    def draw_deposit(self, deposit_id, tonnes):
        self.drawn.append((deposit_id, tonnes))

    def send(self, command):   # the felled-timber commands: no recipe here fells wood
        return None

    def view(self, name):
        return lambda: {}


class SiteLimitTests(unittest.TestCase):
    def test_only_ore_recipes_are_sited_and_each_tile_holds_a_limit_from_its_deposits(self):
        host = Host([deposit("a", "t1", 500.0, 9000.0, grade=500.0), deposit("b", "t1", 100.0, 9000.0),
                     deposit("c", "t2", 50.0, 9000.0)])
        limits = economy_port_sites.site_limits(host, OUTPUTS)
        self.assertEqual({limit.recipe_id for limit in limits}, {ORE})
        # a tonne of ore a run is one thousand kilograms; grade 500 kg a tonne raises two tonnes of ore per tonne held
        self.assertEqual({limit.tile: limit.capacity_runs_per_year for limit in limits},
                         {"t1": 500.0 * 2.0 + 100.0, "t2": 50.0})

    def test_a_tile_whose_deposit_is_worked_out_keeps_a_limit_of_nothing(self):
        limits = economy_port_sites.site_limits(Host([deposit("a", "t1", 0.0, 0.0)]), OUTPUTS)
        self.assertEqual([(limit.tile, limit.capacity_runs_per_year) for limit in limits], [("t1", 0.0)])


class DepletionTests(unittest.TestCase):
    def test_what_firms_raise_on_a_tile_is_drawn_from_its_deposits_largest_first(self):
        host = Host([deposit("small", "t1", 500.0, 10.0), deposit("big", "t1", 500.0, 900.0, grade=500.0)])
        economy_port_sites.deplete(host, {(ORE, "t1"): 50.0}, OUTPUTS)
        # fifty runs raise fifty tonnes of ore: twenty-five tonnes of the big deposit, at two tonnes of ore a tonne
        self.assertEqual(host.drawn, [("big", 25.0)])

    def test_what_one_deposit_cannot_give_is_drawn_from_the_next(self):
        host = Host([deposit("small", "t1", 500.0, 10.0), deposit("big", "t1", 500.0, 30.0)])
        economy_port_sites.deplete(host, {(ORE, "t1"): 35.0}, OUTPUTS)
        self.assertEqual(host.drawn, [("big", 30.0), ("small", 5.0)])

    def test_nothing_is_drawn_for_a_recipe_that_is_not_ore_or_a_tile_with_no_deposit(self):
        host = Host([deposit("a", "t1", 500.0, 900.0)])
        economy_port_sites.deplete(host, {("bread_kg", "t1"): 10.0, (ORE, "no_such_tile"): 10.0}, OUTPUTS)
        self.assertEqual(host.drawn, [])


if __name__ == "__main__":
    unittest.main()
