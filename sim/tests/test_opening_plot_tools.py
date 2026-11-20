"""The opening gives a household the tools its own-plot hours keep in use and sizes their makers on the yearly wear, so the
first year's tool bids replace wear and do not buy the whole stock. Each test calls one function on written-out inputs."""
QUICK_TOPIC = True

import unittest

from sim.economy import opening_plot_tools
from sim.economy.tool_wear import tool_bids
from sim.economy.types import EDGE_PRODUCTION, GoodSpec, Recipe
from sim.markets.port_setup import tool_wear_recipes

HOURS_PER_YEAR = 2000.0
LIFE = 5.0
STOCK = 2.0      # spades one worker keeps in use, so a year of one worker wears STOCK / LIFE of them
SPECS = {"spade": GoodSpec("spade", 1.0, 0.0, LIFE, "tool"), "grain": GoodSpec("grain", 1.0, 0.0, 0.0, "food")}
RECIPES = tool_wear_recipes(
    {"farm": Recipe("farm", {"grain": 10.0}, {"seed": 1.0}, {"hand": HOURS_PER_YEAR}),
     "spade": Recipe("spade", {"spade": 1.0}, {}, {"smith": 10.0})},
    {"hand": {"tool_basket": ["spade"], "tool_stock_per_worker": {"spade": STOCK}}}, {"spade": LIFE}, HOURS_PER_YEAR)
PRICED = {"spade": 5.0, "grain": 2.0}


class StockTests(unittest.TestCase):
    def test_a_plot_worked_a_whole_year_keeps_one_workers_stock_in_use(self):
        self.assertEqual(opening_plot_tools.stock_by_good({"farm": HOURS_PER_YEAR}, RECIPES, SPECS), {"spade": STOCK})

    def test_half_the_hours_keep_half_the_stock(self):
        self.assertEqual(opening_plot_tools.stock_by_good({"farm": HOURS_PER_YEAR / 2.0}, RECIPES, SPECS), {"spade": STOCK / 2.0})

    def test_no_plot_hours_keep_no_stock(self):
        self.assertEqual(opening_plot_tools.stock_by_good({}, RECIPES, SPECS), {})


class WearTests(unittest.TestCase):
    def test_a_year_wears_the_stock_over_its_life(self):
        self.assertEqual(opening_plot_tools.yearly_wear({"spade": STOCK}, SPECS), {"spade": STOCK / LIFE})


class FirstYearBidTests(unittest.TestCase):
    def test_a_household_holding_the_stock_bids_for_one_years_wear(self):
        bids = tool_bids("household", "tile", lambda good: "area", lambda good: PRICED[good], lambda good: STOCK,
                         RECIPES, {"farm": HOURS_PER_YEAR}, SPECS, 1000.0)
        self.assertAlmostEqual(sum(bid.floor_quantity for bid in bids), STOCK / LIFE)

    def test_a_household_holding_none_bids_for_the_whole_stock(self):
        bids = tool_bids("household", "tile", lambda good: "area", lambda good: PRICED[good], lambda good: 0.0,
                         RECIPES, {"farm": HOURS_PER_YEAR}, SPECS, 1000.0)
        self.assertAlmostEqual(sum(bid.floor_quantity for bid in bids), STOCK)


class DemandTests(unittest.TestCase):
    def test_the_wear_of_each_cohorts_plot_tools_joins_its_tiles_final_demand(self):
        final = {"north": {"grain": 5.0}}
        opening_plot_tools.add_wear(final, {"a": "north", "b": "south"},
                                    {"a": {"farm": HOURS_PER_YEAR}, "b": {"farm": HOURS_PER_YEAR / 2.0}}, RECIPES, SPECS, PRICED)
        self.assertEqual(final, {"north": {"grain": 5.0, "spade": STOCK / LIFE}, "south": {"spade": STOCK / LIFE / 2.0}})

    def test_a_tool_with_no_opening_price_is_left_out(self):
        final = {"north": {"grain": 5.0}}
        opening_plot_tools.add_wear(final, {"a": "north"}, {"a": {"farm": HOURS_PER_YEAR}}, RECIPES, SPECS, {"grain": 2.0})
        self.assertEqual(final, {"north": {"grain": 5.0}})


class SeedTests(unittest.TestCase):
    def test_each_cohort_is_given_the_stock_its_plot_hours_keep_in_use(self):
        moves = opening_plot_tools.seed_moves({"a": "north", "b": "south"}, {"a": {"farm": HOURS_PER_YEAR}, "b": {}},
                                              RECIPES, SPECS, PRICED)
        self.assertEqual([(move.giver, move.receiver, move.good, move.tile, move.quantity) for move in moves],
                         [(EDGE_PRODUCTION, "a", "spade", "north", STOCK)])

    def test_a_tool_with_no_opening_price_is_not_given(self):
        self.assertEqual(opening_plot_tools.seed_moves({"a": "north"}, {"a": {"farm": HOURS_PER_YEAR}}, RECIPES, SPECS, {}), [])


if __name__ == "__main__":
    unittest.main()
