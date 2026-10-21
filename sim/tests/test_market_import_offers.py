"""Complaint 673: an importer offers at its landed cost. Cargo cheaper than the local producers' floor sells
first and sets the price for the quantity it covers; locals supply the rest at their floor; cargo dearer than
the floor is an ordinary offer. Pure tests of sim/world/market.py."""

QUICK_TOPIC = True

import unittest

from sim.world import market
from sim.world.producer_market import Offer


def conditions(**changes):
    base = dict(household_demand_at_anchor_tonnes=100.0, committed_demand_tonnes=0.0,
                society_capacity_tonnes=100.0, actor_supply_tonnes=0.0,
                founder_sales_tonnes=0.0, stock_tonnes=0.0,
                demand_price_elasticity=0.5, floor_ratio=0.8, ceiling_ratio=6.0)
    base.update(changes)
    return market.MarketConditions(**base)


class ImportOffersTests(unittest.TestCase):
    def test_cargo_cheaper_than_the_floor_lowers_the_price_for_its_quantity(self):
        without = market.clear_market(conditions())
        cargo = market.clear_market(conditions(imports=(Offer(20.0, 0.5),)))
        self.assertLess(cargo.price_ratio, without.price_ratio)
        self.assertAlmostEqual(cargo.imports_sold_tonnes, 20.0, places=6)
        self.assertLess(cargo.society_sales_tonnes, without.society_sales_tonnes)

    def test_price_is_the_cargo_price_where_it_covers_the_demand(self):
        outcome = market.clear_market(conditions(imports=(Offer(500.0, 0.5),)))
        self.assertAlmostEqual(outcome.price_ratio, 0.5, places=6)
        self.assertAlmostEqual(outcome.society_sales_tonnes, 0.0, places=6)
        self.assertGreater(outcome.held_over_tonnes, 0.0)   # the cargo the market did not take

    def test_cargo_dearer_than_the_floor_does_not_lower_the_price(self):
        without = market.clear_market(conditions())
        dear = market.clear_market(conditions(imports=(Offer(20.0, 1.5),)))
        self.assertGreaterEqual(dear.price_ratio, without.price_ratio - 1e-9)
        self.assertAlmostEqual(dear.imports_sold_tonnes, 0.0, places=6)

    def test_the_cheaper_of_two_carriers_sells_first(self):
        outcome = market.clear_market(conditions(
            household_demand_at_anchor_tonnes=30.0, society_capacity_tonnes=0.0,
            imports=(Offer(25.0, 0.7), Offer(25.0, 0.4))))
        both = market.clear_market(conditions(
            household_demand_at_anchor_tonnes=30.0, society_capacity_tonnes=0.0, imports=(Offer(25.0, 0.4),)))
        self.assertGreater(outcome.price_ratio, both.price_ratio)
        self.assertAlmostEqual(outcome.imports_sold_tonnes, outcome.quantity_traded_tonnes, places=6)

    def test_a_cargo_sold_never_exceeds_the_demand(self):
        outcome = market.clear_market(conditions(imports=(Offer(1e6, 0.5),)))
        self.assertLessEqual(outcome.imports_sold_tonnes, outcome.quantity_traded_tonnes + 1e-9)


if __name__ == "__main__":
    unittest.main()
