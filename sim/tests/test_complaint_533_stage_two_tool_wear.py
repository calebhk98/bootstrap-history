"""Complaint 533, stage 2: the tools a trade's workers wear out are bought on the goods market, by the employer
(as an input of its recipe) and by a household working its own plot (as a durable it keeps in use). Each test calls
the rule on built inputs."""
QUICK_TOPIC = True

import unittest

from sim.economy import households_own, producers
from sim.economy.tool_wear import tool_bids, with_tool_wear
from sim.economy.types import GoodSpec, Recipe
from sim.markets.port_setup import tool_wear_recipes

HOURS_PER_YEAR = 2000.0
LIFE = 5.0
STOCK = 2.0
REGISTRY = {"hand": {"tool_basket": ["spade"], "tool_stock_per_worker": {"spade": STOCK}},
            "idler": {"tool_basket": []}}
LIVES = {"spade": LIFE}


def recipe(trade="hand", workers=1.0, outputs=None):
    return Recipe("farm", outputs or {"grain": 10.0}, {"seed": 1.0}, {trade: workers * HOURS_PER_YEAR})


def specs():
    return {"spade": GoodSpec("spade", 1.0, 0.0, LIFE, "tool"), "grain": GoodSpec("grain", 1.0, 0.0, 0.0, "food")}


def worn_recipe(base):
    return tool_wear_recipes({"farm": base, "spade": Recipe("spade", {"spade": 1.0}, {}, {"smith": 10.0})},
                             REGISTRY, LIVES, HOURS_PER_YEAR)["farm"]


class View:
    year = 3

    def price(self, good, area):
        return {"grain": 2.0, "seed": 1.0, "spade": 5.0}.get(good)

    def wage(self, trade, area):
        return 0.001

    def interest_rate(self, currency):
        return 0.05

    def area_of(self, good, tile):
        return "area"

    def currency_of(self, area):
        return "coin"

    def stock(self, agent, good, tile):
        return 0.0


class EmployerTests(unittest.TestCase):
    def test_an_employer_of_n_workers_buys_n_times_stock_over_life_a_year(self):
        for workers in (1.0, 7.0):
            worn = worn_recipe(recipe(workers=workers))
            self.assertAlmostEqual(worn.inputs["spade"], workers * STOCK / LIFE)
            self.assertAlmostEqual(worn.tool_wear["spade"], workers * STOCK / LIFE)
            self.assertEqual(worn.inputs["seed"], 1.0)

    def test_the_plan_bids_for_the_wear_through_the_ordinary_input_path(self):
        worn = worn_recipe(recipe(workers=5.0))
        who = producers.Producer("f1", "lord", "farm", "t", capacity_runs=3.0, expected_prices={"grain": 2.0})
        plan = producers.plan(who, worn, View(), 1e6)
        self.assertGreater(plan.runs, 0.0)
        bid = [each for each in plan.bids if each.good == "spade"][0]
        self.assertAlmostEqual(bid.floor_quantity, plan.runs * 5.0 * STOCK / LIFE)

    def test_a_trade_with_no_basket_buys_none(self):
        for trade in ("idler", "unlisted"):
            worn = worn_recipe(recipe(trade=trade, workers=4.0))
            self.assertNotIn("spade", worn.inputs)
            self.assertEqual(dict(worn.tool_wear), {})

    def test_a_tool_nothing_makes_is_not_charged_and_a_toolmaker_does_not_wear_its_own(self):
        wear = {"hand": {"spade": 1.0}}
        self.assertEqual(with_tool_wear(recipe(), wear, makeable=()).inputs, {"seed": 1.0})
        self.assertNotIn("spade", with_tool_wear(recipe(outputs={"spade": 1.0}), wear, makeable=["spade"]).inputs)


class OwnPlotTests(unittest.TestCase):
    def bids(self, hours, held=0.0, cash=1e6):
        worn = worn_recipe(recipe())
        return tool_bids("home", "t", lambda good: "area", lambda good: View().price(good, "area"), lambda good: held,
                         {"farm": worn}, {"farm": hours}, specs(), cash)

    def test_a_household_buys_tools_in_proportion_to_the_hours_it_works(self):
        small = self.bids(HOURS_PER_YEAR)[0].floor_quantity
        large = self.bids(3.0 * HOURS_PER_YEAR)[0].floor_quantity
        self.assertAlmostEqual(small, STOCK)             # nothing held: the stock one worker keeps in use
        self.assertAlmostEqual(large, 3.0 * small)

    def test_once_it_holds_the_stock_it_buys_only_what_wore_out(self):
        quantity = self.bids(HOURS_PER_YEAR, held=STOCK)[0].floor_quantity
        self.assertAlmostEqual(quantity, STOCK / LIFE)

    def test_no_hours_no_tools_and_the_budget_never_exceeds_cash(self):
        self.assertEqual(self.bids(0.0), [])
        self.assertLessEqual(sum(bid.budget for bid in self.bids(HOURS_PER_YEAR, cash=3.0)), 3.0 + 1e-9)

    def test_an_own_plot_recipe_may_take_only_its_tool_wear_as_input(self):
        worn = Recipe("farm", {"grain": 10.0}, {"spade": 0.4}, {"hand": 100.0}, tool_wear={"spade": 0.4})
        bought = Recipe("farm2", {"grain": 10.0}, {"spade": 0.4, "seed": 1.0}, {"hand": 100.0}, tool_wear={"spade": 0.4})

        class Need:
            need_id = "food"
            goods = [("grain", 1.0)]
        basket = type("Basket", (), {"needs": [Need()]})()
        options = households_own.own_production_options({"farm": worn, "farm2": bought}, {"farm": 1.0, "farm2": 1.0}, basket)
        self.assertEqual([row[1] for row in options["food"]], ["farm"])


if __name__ == "__main__":
    unittest.main()
