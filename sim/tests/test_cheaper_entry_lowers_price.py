"""Complaint 640 (from 558): a cheaper making cost lowers the price an entrant can offer, and a lower price clears
more where demand slopes down. Two rules, each called on built inputs:

1. `entry_trial.full_cost_per_unit`: halving a recipe's labour hours takes off half the labour's share of its cost.
2. `goods_market.clear_at_one_price`: an entrant offering at its lower cost moves the cleared price down and the cleared quantity
   up once its stock reaches past the marginal incumbent; a stock short of that leaves the price alone (the entrant
   is under the margin), and where demand does not slope the price falls but the quantity does not.

Replaces the whole-game topic real_output_cheaper_entry, whose entrant was under a percent of the market and was lost
in the economy's own divergence between two runs."""
QUICK_TOPIC = True

import unittest

from sim.economy.entry_trial import full_cost_per_unit
from sim.economy.goods_market import clear_at_one_price as clear
from sim.economy.types import Bid, Offer, Recipe

GOOD, AREA, TILE = "stone_blocks", "area", "tile"
INCUMBENT_COST = 1.0
MARGINAL_INCUMBENT_COST = 1.3
INCUMBENT_STOCK = 60.0


def recipe(labour_hours):
    return Recipe("blocks", {GOOD: 1.0}, {"fuel": 2.0}, {"mason": labour_hours})


def cost_of(labour_hours):
    return full_cost_per_unit(recipe(labour_hours), GOOD, {GOOD: 1.0}, {"fuel": 0.5}, {"mason": 0.25}, 0.0)


def demand(elasticity=0.5):
    return [Bid("buyers", GOOD, AREA, TILE, 0.0, 100.0, 1.0, elasticity, 1e9)]


def incumbents():
    return [Offer("first", GOOD, AREA, TILE, INCUMBENT_STOCK, INCUMBENT_COST),
            Offer("marginal", GOOD, AREA, TILE, INCUMBENT_STOCK, MARGINAL_INCUMBENT_COST)]


def cleared(offers, elasticity=0.5):
    return clear(demand(elasticity), offers, GOOD, AREA, "coin", None)


def with_entrant(stock, reservation):
    return incumbents() + [Offer("entrant", GOOD, AREA, TILE, stock, reservation)]


class EntryCostTests(unittest.TestCase):
    def test_halving_the_labour_takes_off_half_the_labours_share_of_the_cost(self):
        full, halved = cost_of(8.0), cost_of(4.0)
        labour_share = 8.0 * 0.25 / full
        self.assertGreater(labour_share, 0.0)
        self.assertAlmostEqual(halved / full, 1.0 - labour_share / 2.0, places=9)

    def test_less_labour_costs_less(self):
        self.assertLess(cost_of(7.0), cost_of(8.0))


class ClearingWithACheaperEntrantTests(unittest.TestCase):
    def test_an_entrant_past_the_margin_lowers_the_price_and_clears_more(self):
        before = cleared(incumbents())
        after = cleared(with_entrant(30.0, 0.5 * INCUMBENT_COST))
        self.assertLess(after.price, before.price)
        self.assertGreater(after.quantity, before.quantity)

    def test_an_entrant_under_the_margin_leaves_the_price_and_quantity_alone(self):
        before = cleared(incumbents())
        after = cleared(with_entrant(5.0, 0.5 * INCUMBENT_COST))
        self.assertEqual(after.price, before.price)
        self.assertEqual(after.quantity, before.quantity)

    def test_an_entrant_no_cheaper_than_the_marginal_incumbent_changes_nothing(self):
        before = cleared(incumbents())
        after = cleared(with_entrant(30.0, MARGINAL_INCUMBENT_COST))
        self.assertEqual(after.price, before.price)
        self.assertEqual(after.quantity, before.quantity)

    def test_a_cheaper_entrant_of_the_same_stock_never_raises_the_price_or_lowers_the_quantity(self):
        costs = [1.25, 1.0, 0.8, 0.5, 0.25]
        results = [cleared(with_entrant(30.0, cost)) for cost in costs]
        for dearer, cheaper in zip(results, results[1:]):
            self.assertLessEqual(cheaper.price, dearer.price)
            self.assertGreaterEqual(cheaper.quantity, dearer.quantity)

    def test_where_demand_does_not_slope_the_price_falls_but_the_quantity_does_not(self):
        before = cleared(incumbents(), elasticity=0.0)
        after = cleared(with_entrant(50.0, 0.5 * INCUMBENT_COST), elasticity=0.0)
        self.assertLess(after.price, before.price)
        self.assertAlmostEqual(after.quantity, before.quantity, places=9)


if __name__ == "__main__":
    unittest.main()
