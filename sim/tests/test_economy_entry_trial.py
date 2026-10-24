"""Trial newcomers: judged at their own cost, only for a market with buyers and no maker in its area."""

QUICK_TOPIC = True

import math
import types
import unittest
from unittest import mock

from sim.economy import entry_trial
from sim.economy.producers import Producer
from sim.economy.types import Bid, Recipe

SMELT = Recipe("smelt", {"metal": 10.0, "slag": 90.0}, {"ore": 100.0}, {"smith": 5.0},
               plant_goods={"stone": 2.0}, plant_life_years=10.0)


def bid(floor, budget, flexible=0.0):
    return Bid("buyer", "grain", "area", "tile", floor, flexible, 1.0, 2.0, budget)


class FullCostTests(unittest.TestCase):
    def test_cost_shares_a_joint_run_by_value_and_counts_the_plant(self):
        prices = {"metal": 9.0, "slag": 0.1}
        cost = entry_trial.full_cost_per_unit(SMELT, "metal", prices, {"ore": 0.5, "stone": 1.0}, {"smith": 2.0}, 0.0)
        run_cost = 100.0 * 0.5 + 5.0 * 2.0 + 2.0 * 1.0 / 10.0
        share = 90.0 / (90.0 + 9.0)
        self.assertAlmostEqual(cost, run_cost * share / 10.0)

    def test_an_input_with_no_price_cannot_be_costed(self):
        self.assertTrue(math.isinf(entry_trial.full_cost_per_unit(SMELT, "metal", {"metal": 9.0}, {}, {"smith": 2.0}, 0.0)))


class DemandAtTests(unittest.TestCase):
    def test_a_floor_stays_a_floor_and_spending_beyond_it_buys_more_at_a_lower_price(self):
        self.assertAlmostEqual(entry_trial.demand_at([bid(10.0, 20.0)], 1.0, 2.0), 10.0)
        self.assertAlmostEqual(entry_trial.demand_at([bid(0.0, 20.0, flexible=20.0)], 1.0, 2.0), 20.0)

    def test_a_buyer_with_a_floor_and_a_budget_takes_no_more_than_its_floor_of_a_good_that_costs_nothing(self):
        # a by-product priced near zero (straw): the budget divided by the price is not what a buyer would take
        self.assertAlmostEqual(entry_trial.demand_at([bid(100.0, 1e5)], 1e-15, 1e-15), 100.0)


class CapacityTests(unittest.TestCase):
    def test_capacity_counts_only_makers_on_the_area_tiles_and_plant_to_come(self):
        farm = Recipe("farm", {"grain": 2.0}, {}, {})
        producers = {"a": Producer("a", "owner", "farm", "t1", 3.0, yield_factor=0.5),
                     "b": Producer("b", "owner", "farm", "t2", 4.0)}
        terms = entry_trial.capacity_terms_by_good(producers, {"farm": farm}, {"a": 1.0})
        self.assertAlmostEqual(entry_trial.capacity_in_area(terms, "grain", ["t1"]), (3.0 * 0.5 + 1.0) * 2.0)
        self.assertAlmostEqual(entry_trial.capacity_in_area(terms, "grain", ["t1", "t2"]), 5.0 + 8.0)
        self.assertEqual(entry_trial.capacity_in_area(terms, "grain", ["t3"]), 0.0)
        self.assertEqual(entry_trial.capacity_in_area(terms, "iron", ["t1"]), 0.0)

    def test_capacity_is_the_same_whatever_order_the_producers_were_made_in(self):
        # a producer dict is in creation order live and in id order once loaded; the sum must not tell them apart
        farm = Recipe("farm", {"grain": 1.0}, {}, {})
        capacities = {"a": 1e16, "b": 1.0, "c": -1e16, "d": 1.0}
        in_order = {name: Producer(name, "owner", "farm", "t1", runs) for name, runs in capacities.items()}
        shuffled = {name: in_order[name] for name in ["c", "a", "d", "b"]}
        totals = [entry_trial.capacity_in_area(entry_trial.capacity_terms_by_good(each, {"farm": farm}, {}), "grain", ["t1"])
                  for each in (in_order, shuffled)]
        self.assertEqual(totals[0], totals[1])


GOOD, MAKE = "metal", "smelt_metal"
MAKE_RECIPE = Recipe(MAKE, {GOOD: 1.0}, {"ore": 1000.0}, {"smith": 30.0})
ANCHOR = "town"


def market(makers=False, price=None):
    """(setup, record, view, area_map) for a metal market of one area and one tile; `makers` puts a smelter there."""
    setup = types.SimpleNamespace(recipes={MAKE: MAKE_RECIPE})
    producers = {"smelter": Producer("smelter", "owner", MAKE, ANCHOR, 3.0)} if makers else {}
    record = types.SimpleNamespace(producers=producers, expansion_runs={})
    area = types.SimpleNamespace(area_id="area", anchor_tile=ANCHOR, tiles=(ANCHOR,))
    area_map = types.SimpleNamespace(goods=lambda: [GOOD], areas=lambda good: [area])
    return setup, record, types.SimpleNamespace(price=lambda good, area_id: price), area_map


def trial_plans(bids, makers=False, siting=None, cost=80.0):
    """trial_entry_plans for `bids` in the metal market, the cheapest recipe costing `cost` a unit (recipes_by_cost is tested above)."""
    setup, record, view, area_map = market(makers)
    with mock.patch.object(entry_trial, "recipes_by_cost", lambda *_args: [(MAKE, cost)]):
        return entry_trial.trial_entry_plans(setup, record, view, area_map, {(GOOD, "area"): bids}, siting=siting)


def metal_bid(floor, ceiling=1000.0):
    return Bid("buyer", GOOD, "area", ANCHOR, floor, 0.0, 95.0, 1.0, 1e9, 0, ceiling)


class RecipesByCostTests(unittest.TestCase):
    def ranked(self, recipes, input_prices):
        setup = types.SimpleNamespace(recipes=recipes, currency_id="coin")
        view = types.SimpleNamespace(interest_rate=lambda currency: 0.05, price=lambda good, area: 100.0, area_of=lambda good, tile: "area")
        with mock.patch.object(entry_trial, "site_rent_per_run", lambda *_args: 0.0), \
                mock.patch.object(entry_trial, "live_input_prices_at", lambda *_args: input_prices), \
                mock.patch.object(entry_trial, "live_wages_at", lambda *_args: {"smith": 1.0}):
            return entry_trial.recipes_by_cost(setup, None, view, GOOD, ANCHOR, sorted(recipes))

    def test_recipes_come_cheapest_first_at_their_full_cost_a_unit(self):
        dear = Recipe("dear", {GOOD: 1.0}, {"ore": 2000.0}, {"smith": 30.0})
        found = self.ranked({MAKE: MAKE_RECIPE, "dear": dear}, {"ore": 0.05})
        self.assertEqual([recipe_id for recipe_id, _cost in found], [MAKE, "dear"])
        self.assertAlmostEqual(found[0][1], 1000.0 * 0.05 + 30.0)

    def test_a_recipe_with_an_unpriced_input_is_left_out(self):
        self.assertEqual(self.ranked({MAKE: MAKE_RECIPE}, {}), [])


class TrialPlanTests(unittest.TestCase):
    def test_no_newcomer_where_no_buyer_bid(self):
        self.assertEqual(trial_plans([]), [])

    def test_no_trial_newcomer_where_the_area_has_a_maker(self):
        self.assertEqual(trial_plans([metal_bid(1000.0)], makers=True), [])


class UnmetBidsDrawAMakerTests(unittest.TestCase):
    """Complaint 473: entry follows the bids' ceilings and quantities against the recipe's computed cost, for any good."""

    def test_bids_with_a_ceiling_under_the_recipes_entry_price_draw_no_maker(self):
        self.assertEqual(trial_plans([metal_bid(50.0, ceiling=1.0)]), [])

    def test_bids_that_meet_the_entry_price_draw_a_maker_sized_by_their_quantity(self):
        small, large = trial_plans([metal_bid(50.0)]), trial_plans([metal_bid(100.0)])
        self.assertEqual(len(small), 1)
        self.assertEqual(small[0].tile, ANCHOR)
        self.assertAlmostEqual(large[0].runs, 2.0 * small[0].runs)

    def test_a_trial_newcomer_is_built_where_the_siting_puts_it(self):
        # beside its inputs, which can be another market area: the area's buyers then wait on carriage (Complaint 473)
        plans = trial_plans([metal_bid(50.0)], siting=lambda recipe_id, demand, runs: ("hills", runs))
        self.assertEqual([plan.tile for plan in plans], ["hills"])

    def test_a_maker_is_planned_only_when_the_bids_ceiling_is_over_its_cost_with_the_entry_margin(self):
        dear = 1000.0 / (1.0 + entry_trial.ENTRY_PRICE_MARGIN_SHARE) + 1.0       # entry price just over the ceiling
        self.assertEqual(trial_plans([metal_bid(50.0)], cost=dear), [])


if __name__ == "__main__":
    unittest.main()
