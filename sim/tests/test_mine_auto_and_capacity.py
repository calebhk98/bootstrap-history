"""Complaints 65 and 67: the automatic mining order counts shafts still being sunk, and a material fed by two supply
tags shows both demands in one capacity row. The rules are called on given numbers."""

QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.materials import rules
from sim.materials.constants import FIREWOOD_PER_CHARCOAL_MASS_RATIO
from sim.resources.api import AutoMothballMines
from sim.resources.module import Resources
from sim.tests import module_harness
from sim.resources.sizing import auto_mine_affordable_tonnes, auto_mine_order_tonnes

RICH = 1e12
CAPEX = 100.0


class AutoMineOrder(unittest.TestCase):

    def test_pending_capacity_covering_the_shortfall_orders_nothing(self):
        self.assertEqual(auto_mine_order_tonnes(1000.0, 200.0, 800.0, RICH, CAPEX), 0.0)

    def test_working_capacity_covering_the_shortfall_orders_nothing(self):
        self.assertEqual(auto_mine_order_tonnes(1000.0, 1500.0, 0.0, RICH, CAPEX), 0.0)

    def test_a_shaft_already_sinking_lowers_the_order_by_its_tonnes(self):
        bare = auto_mine_order_tonnes(1000.0, 0.0, 0.0, RICH, CAPEX)
        partial = auto_mine_order_tonnes(1000.0, 0.0, 400.0, RICH, CAPEX)
        self.assertEqual(bare, 1000.0)
        self.assertEqual(partial, 600.0)

    def test_the_order_never_exceeds_what_the_purse_sinks(self):
        order = auto_mine_order_tonnes(1000.0, 0.0, 0.0, 10_000.0, CAPEX)
        self.assertEqual(order, auto_mine_affordable_tonnes(10_000.0, CAPEX))
        self.assertLess(order, 1000.0)

    def test_a_dearer_mine_is_affordable_in_fewer_tonnes(self):
        self.assertLess(auto_mine_affordable_tonnes(10_000.0, 2 * CAPEX), auto_mine_affordable_tonnes(10_000.0, CAPEX))

    def test_a_free_mine_does_not_divide_by_zero(self):
        self.assertGreater(auto_mine_affordable_tonnes(10_000.0, 0.0), 0.0)


class StubSupply:
    """The real shared-land arithmetic over given own supply by tag."""

    def __init__(self, own_by_tag):
        self.own_by_tag = own_by_tag

    def demand_and_own_supply_by_material(self, by_tag):
        return rules.demand_and_own_supply(by_tag, lambda tag: self.own_by_tag.get(tag, 0.0))


class SharedForestRow(unittest.TestCase):
    RATIO = FIREWOOD_PER_CHARCOAL_MASS_RATIO

    def test_charcoal_and_firewood_demands_add_in_one_row(self):
        supply = StubSupply({"forest": 100.0, "forest4": 100.0 / self.RATIO})
        totals = supply.demand_and_own_supply_by_material({("charcoal", "forest"): 500.0, ("charcoal", "forest4"): 500.0})
        demand, own = totals["charcoal"]
        self.assertGreater(demand, 500.0)
        self.assertAlmostEqual(demand, 500.0 + 500.0 / self.RATIO)

    def test_tags_on_one_land_base_do_not_add_their_own_supply(self):
        supply = StubSupply({"forest": 100.0, "forest4": 100.0 / self.RATIO})
        _demand, own = supply.demand_and_own_supply_by_material(
            {("charcoal", "forest"): 1.0, ("charcoal", "forest4"): 1.0})["charcoal"]
        self.assertAlmostEqual(own, 100.0)

    def test_a_small_firewood_demand_does_not_hide_a_large_charcoal_shortfall(self):
        supply = StubSupply({"forest": 100.0, "forest4": 100.0 / self.RATIO})
        demand, own = supply.demand_and_own_supply_by_material(
            {("charcoal", "forest"): 5000.0, ("charcoal", "forest4"): 10.0})["charcoal"]
        self.assertGreater(demand, own)

    def test_a_small_charcoal_demand_does_not_hide_a_large_firewood_shortfall(self):
        supply = StubSupply({"forest": 100.0, "forest4": 100.0 / self.RATIO})
        demand, own = supply.demand_and_own_supply_by_material(
            {("charcoal", "forest"): 10.0, ("charcoal", "forest4"): 5000.0})["charcoal"]
        self.assertGreater(demand, own)


class AutoMothball(unittest.TestCase):
    def run_policy(self, balance=-5.0, capacity=None, policy=None):
        mothballed = []
        resources = module_harness.build(Resources, views={"acting_balance": lambda: balance, "founder": lambda: {"policy": {} if policy is None else policy}})
        resources.mine_capacity = lambda: {"iron": 3.0} if capacity is None else capacity
        resources.mothball_mines = lambda: mothballed.append(True)
        resources.auto_mothball_mines(AutoMothballMines())
        return mothballed

    def test_a_negative_balance_with_workings_mothballs_them_unless_the_seat_set_it_off(self):
        self.assertEqual(self.run_policy(), [True])
        self.assertEqual(self.run_policy(policy={"auto_mothball": False}), [])

    def test_nothing_is_mothballed_with_a_balance_at_zero_or_no_workings(self):
        self.assertEqual((self.run_policy(balance=0.0), self.run_policy(capacity={})), ([], []))


if __name__ == "__main__":
    unittest.main()
