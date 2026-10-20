"""Trial newcomers: judged at their own cost, only for a market with buyers and no maker in its area."""

QUICK_TOPIC = True

import math
import unittest

from sim.economy import entry_trial
from sim.economy.economy import Economy
from sim.economy.producers import Producer
from sim.economy.types import Bid, Recipe
from sim.tests import economy_fixture as fixture

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


class TrialPlanTests(unittest.TestCase):
    def test_no_newcomer_where_no_buyer_bid(self):
        setup = fixture.small_setup()
        economy = Economy(setup)
        economy.step(fixture.quiet_year(setup))
        bids = {(fixture.GRAIN, area.area_id): [] for area in economy.area_map.areas(fixture.GRAIN)}
        self.assertEqual(entry_trial.trial_entry_plans(setup, economy.record, economy.view(), economy.area_map, bids), [])

    def test_no_trial_newcomer_where_the_area_has_a_maker(self):
        setup = fixture.small_setup()
        economy = Economy(setup)
        economy.step(fixture.quiet_year(setup))
        bids = {(fixture.GRAIN, area.area_id): [bid(1000.0, 1e9)] for area in economy.area_map.areas(fixture.GRAIN)}
        self.assertEqual(entry_trial.trial_entry_plans(setup, economy.record, economy.view(), economy.area_map, bids), [])


class UnmetBidsDrawAMakerTests(unittest.TestCase):
    """Complaint 473: entry follows the bids' ceilings and quantities against the recipe's computed cost, for any good."""

    def setUp(self):
        self.setup = fixture.small_setup()
        economy = Economy(self.setup)
        economy.step(fixture.quiet_year(self.setup))
        for producer_id in [each for each, producer in economy.record.producers.items()
                            if producer.recipe_id == fixture.SMELT]:
            del economy.record.producers[producer_id]
        self.economy = economy
        self.area = economy.area_map.areas(fixture.METAL)[0]

    def plans(self, floor, ceiling, siting=None):
        bid = Bid("buyer", fixture.METAL, self.area.area_id, self.area.anchor_tile, floor, 0.0, 95.0, 1.0, 1e9, 0, ceiling)
        return entry_trial.trial_entry_plans(self.setup, self.economy.record, self.economy.view(), self.economy.area_map,
                                             {(fixture.METAL, self.area.area_id): [bid]}, siting=siting)

    def test_bids_with_a_ceiling_under_the_recipes_entry_price_draw_no_maker(self):
        self.assertEqual(self.plans(50.0, 1.0), [])

    def test_bids_that_meet_the_entry_price_draw_a_maker_sized_by_their_quantity(self):
        small, large = self.plans(50.0, 1000.0), self.plans(100.0, 1000.0)
        self.assertEqual(len(small), 1)
        self.assertEqual(small[0].tile, self.area.anchor_tile)
        self.assertAlmostEqual(large[0].runs, 2.0 * small[0].runs)

    def test_a_trial_newcomer_is_built_where_the_siting_puts_it(self):
        # beside its inputs, which can be another market area: the area's buyers then wait on carriage (Complaint 473)
        plans = self.plans(50.0, 1000.0, siting=lambda recipe_id, demand, runs: ("hills", runs))
        self.assertEqual([plan.tile for plan in plans], ["hills"])


if __name__ == "__main__":
    unittest.main()
