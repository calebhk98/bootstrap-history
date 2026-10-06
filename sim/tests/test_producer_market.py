"""Complaint 375: producers offer a quantity at the lowest price each will take (its own cost), the market
clears the offers against demand, and the market module knows nothing of the tech tree.

Pure tests of sim/world/market.py and sim/world/producer_market.py, and a structural test of what the
market modules import."""

QUICK_TOPIC = True

import ast
import os
import unittest

from sim.world import market
from sim.world.producer_market import Offer

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def conditions(**changes):
    base = dict(household_demand_at_anchor_tonnes=65.0, committed_demand_tonnes=0.0,
                society_capacity_tonnes=0.0, actor_supply_tonnes=0.0,
                founder_sales_tonnes=0.0, stock_tonnes=0.0,
                demand_price_elasticity=0.5, floor_ratio=0.4, ceiling_ratio=6.0)
    base.update(changes)
    return market.MarketConditions(**base)


class TwoProducersTests(unittest.TestCase):
    def test_price_clears_between_two_producers_with_different_costs(self):
        cheap, dear = Offer(60.0, 0.8), Offer(60.0, 1.3)
        outcome = market.clear_market(conditions(offers=(cheap, dear)))
        self.assertGreater(outcome.price_ratio, cheap.reservation_ratio)
        self.assertLess(outcome.price_ratio, dear.reservation_ratio)
        self.assertAlmostEqual(outcome.offers_sold_tonnes, 60.0, places=6)    # the dear one sits out

    def test_the_dearer_producer_sells_once_demand_carries_the_price_to_its_cost(self):
        offers = (Offer(60.0, 0.8), Offer(60.0, 1.3))
        outcome = market.clear_market(conditions(offers=offers, household_demand_at_anchor_tonnes=200.0))
        self.assertGreaterEqual(outcome.price_ratio, 1.3 - 1e-9)
        self.assertGreater(outcome.offers_sold_tonnes, 60.0)

    def test_a_producer_never_sells_below_its_cost(self):
        for demand in (10.0, 40.0, 65.0, 120.0, 400.0):
            offers = (Offer(60.0, 0.8), Offer(60.0, 1.3))
            outcome = market.clear_market(conditions(offers=offers, household_demand_at_anchor_tonnes=demand))
            if outcome.offers_sold_tonnes > 60.0 + 1e-9:
                self.assertGreaterEqual(outcome.price_ratio, 1.3 - 1e-9)
            if outcome.offers_sold_tonnes > 1e-9:
                self.assertGreaterEqual(outcome.price_ratio, 0.8 - 1e-9)

    def test_a_negative_reservation_is_not_floored_at_zero(self):
        # a waste by-product costs money to dispose of: it is offered at any price
        outcome = market.clear_market(conditions(offers=(Offer(10.0, -0.2),), household_demand_at_anchor_tonnes=5.0))
        self.assertGreater(outcome.offers_sold_tonnes, 0.0)


class EntrantTests(unittest.TestCase):
    def incumbents(self, **changes):
        return conditions(society_capacity_tonnes=100.0, household_demand_at_anchor_tonnes=100.0, **changes)

    def test_a_cheaper_producer_entering_adds_supply_and_lowers_the_price(self):
        before = market.clear_market(self.incumbents())
        entrant = Offer(30.0, 0.7)
        after = market.clear_market(self.incumbents(offers=(entrant,)))
        self.assertLess(after.price_ratio, before.price_ratio)
        self.assertGreater(after.quantity_traded_tonnes, before.quantity_traded_tonnes)
        self.assertLess(after.society_sales_tonnes, before.society_sales_tonnes)    # it displaces some
        self.assertEqual(entrant, Offer(30.0, 0.7))                                  # its own cost is its own

    def test_an_offer_dearer_than_the_price_changes_nothing(self):
        before = market.clear_market(self.incumbents())
        after = market.clear_market(self.incumbents(offers=(Offer(30.0, 2.5),)))
        self.assertAlmostEqual(before.price_ratio, after.price_ratio, places=9)
        self.assertEqual(after.offers_sold_tonnes, 0.0)


class MarketKnowsNothingOfTheTreeTests(unittest.TestCase):
    PURE = ("sim/world/market.py", "sim/world/producer_market.py")
    ENGINE_MARKET = ("sim/engine/goods_market_api.py", "sim/engine/market_clearing.py",
                     "sim/engine/market_demand.py")
    TREE_MODULES = ("prices", "solve_prices", "solve_prices_core", "solve_prices_reach", "node_output",
                    "techniques_in_use", "concern_volume", "entry_cost", "tree_merge", "catalog", "joint_allocation")
    TREE_WORDS = ("requires_node", "techniques_in_use", "production_entries", "nodes_gated")

    def imported(self, path):
        tree = ast.parse(open(os.path.join(ROOT, path)).read())
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(part for alias in node.names for part in alias.name.split("."))
            elif isinstance(node, ast.ImportFrom):
                names.update((node.module or "").split("."))
                names.update(alias.name for alias in node.names)
        return names

    def test_market_modules_import_nothing_from_the_tech_tree(self):
        for path in self.PURE + self.ENGINE_MARKET:
            leaked = self.imported(path) & set(self.TREE_MODULES)
            self.assertFalse(leaked, "%s imports %s" % (path, sorted(leaked)))
            self.assertNotIn("sim.engine", open(os.path.join(ROOT, path)).read().replace(
                "sim.ui.protocol", "") if path in self.PURE else "")

    def test_market_modules_never_name_tree_things(self):
        for path in self.PURE + self.ENGINE_MARKET:
            source = open(os.path.join(ROOT, path)).read()
            for word in self.TREE_WORDS:
                self.assertNotIn(word, source, "%s names %s" % (path, word))


if __name__ == "__main__":
    unittest.main()
