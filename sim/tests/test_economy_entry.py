"""New makers: where buyers wanted more of a good than was sold, a known way of making it that pays at
the price they bid starts a producer on the market's main tile."""
import unittest

from sim.economy import entry
from sim.economy.types import Bid, Recipe
from sim.tests.test_economy_producers import View

SALT = Recipe("boil_salt", {"salt": 10.0}, {"firewood": 5.0}, {"hand": 2.0}, {"pan": 1.0}, {}, 10.0)
PANEL = Recipe("make_panel", {"panel": 1.0}, {}, {"hand": 1.0})


def market(good="salt", unmet=100.0):
    return {(good, "area"): entry.UnmetDemand(good, "area", "anchor", unmet)}


def plans(recipes, view, unmet):
    return entry.entry_plans(recipes, view, unmet)


class EntryTests(unittest.TestCase):
    def view(self, salt_price):
        return View(prices={"salt": salt_price, "firewood": 0.1, "pan": 2.0}, wages={"hand": 0.2})

    def test_unmet_demand_for_a_good_a_known_recipe_makes_at_a_profit_brings_a_maker(self):
        chosen = plans({"boil_salt": SALT}, self.view(1.0), market())
        self.assertEqual([(plan.recipe_id, plan.tile) for plan in chosen], [("boil_salt", "anchor")])
        expected_runs = 100.0 * entry.ENTRY_SHARE_OF_UNMET_DEMAND / SALT.outputs["salt"]
        self.assertAlmostEqual(chosen[0].runs, expected_runs)

    def test_nobody_enters_where_the_price_does_not_cover_the_cost(self):
        self.assertEqual(plans({"boil_salt": SALT}, self.view(0.05), market()), [])

    def test_a_good_whose_only_recipe_is_not_known_gets_no_maker(self):
        # recipes are what the society knows: panels are wanted but nobody can make them
        self.assertEqual(plans({"boil_salt": SALT}, View(prices={"panel": 100.0}), market("panel")), [])

    def test_makers_with_spare_capacity_cover_the_gap_before_anyone_enters(self):
        # a gap the incumbents could fill from idle capacity brings no newcomer; a larger one brings a
        # newcomer for the rest, even where a maker of the same recipe already works the tile
        self.assertEqual(entry.gap_beyond_spare(100.0, 120.0), 0.0)
        self.assertEqual(entry.gap_beyond_spare(100.0, 30.0), 70.0)

    def test_no_unmet_demand_no_entry(self):
        self.assertEqual(plans({"boil_salt": SALT}, self.view(1.0), market(unmet=0.0)), [])


class UnmetQuantityTests(unittest.TestCase):
    def test_a_market_with_buyers_and_no_sellers_has_its_whole_demand_unmet(self):
        bids = [Bid("b", "salt", "area", "tile", 5.0, 10.0, 1.0, 1.0, 1e9, 0)]
        self.assertAlmostEqual(entry.unmet_quantity(bids, 1.0, 0.0), 15.0)

    def test_a_market_that_sold_what_was_wanted_has_none(self):
        bids = [Bid("b", "salt", "area", "tile", 5.0, 10.0, 1.0, 1.0, 1e9, 0)]
        self.assertEqual(entry.unmet_quantity(bids, 1.0, 15.0), 0.0)


class EntrantLoanTests(unittest.TestCase):
    def test_lenders_advance_no_more_than_the_owner_risks(self):
        # a newcomer with nothing at stake is not lent its whole plant: the loan, and so the size it
        # starts at, is bounded by its owner's stake
        self.assertAlmostEqual(entry.entrant_loan(plant_value=1000.0, owner_stake=100.0),
                               100.0 * entry.ENTRANT_DEBT_PER_STAKE)
        self.assertAlmostEqual(entry.entrant_loan(plant_value=50.0, owner_stake=100.0), 50.0)


class RestakeTests(unittest.TestCase):
    def test_an_owner_puts_working_cash_back_into_a_paying_producer_that_ran_out(self):
        # with no cash it buys no inputs and hires nobody, so without its owner it never runs again
        self.assertAlmostEqual(entry.restake(shortfall=50.0, owner_cash=1000.0, pays=True),
                               min(50.0, entry.ENTRANT_OWNER_STAKE_SHARE * 1000.0))

    def test_no_restake_for_a_producer_whose_runs_lose(self):
        self.assertEqual(entry.restake(shortfall=50.0, owner_cash=1000.0, pays=False), 0.0)

    def test_no_restake_without_a_shortfall(self):
        self.assertEqual(entry.restake(shortfall=0.0, owner_cash=1000.0, pays=True), 0.0)


if __name__ == "__main__":
    unittest.main()
