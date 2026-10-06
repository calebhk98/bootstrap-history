"""Trial newcomers: judged at their own cost, only for a market with buyers and no maker in its area."""

QUICK_TOPIC = True

import math
import unittest

from sim.economy import entry_trial
from sim.economy.economy import Economy
from sim.economy.types import Bid, Recipe
from sim.tests import economy_fixture as fixture

SMELT = Recipe("smelt", {"metal": 10.0, "slag": 90.0}, {"ore": 100.0}, {"smith": 5.0},
               plant_goods={"stone": 2.0}, plant_life_years=10.0)


def bid(floor, budget):
    return Bid("buyer", "grain", "area", "tile", floor, 0.0, 1.0, 2.0, budget)


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
        self.assertAlmostEqual(entry_trial.demand_at([bid(0.0, 20.0)], 1.0, 2.0), 20.0)


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


if __name__ == "__main__":
    unittest.main()
