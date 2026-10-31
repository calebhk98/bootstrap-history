"""Complaint 545: the opening sizes producers for what households buy after their own plots, by the year's rules."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import households_buffer_stock, opening_own, opening_resting, opening_runs, year_goods
from sim.economy.protocols import AgentOrders
from sim.economy.types import Bid, Recipe


def recipes():
    return {"farm": types.SimpleNamespace(labour_hours={"labourer": 10.0})}


class HiredShareTests(unittest.TestCase):
    def test_runs_needing_a_quarter_of_the_hands_hire_a_quarter(self):
        self.assertEqual(opening_own.hired_share({"farm": 5.0}, recipes(), 200.0), 0.25)

    def test_runs_needing_more_than_the_hands_hire_all_of_them(self):
        self.assertEqual(opening_own.hired_share({"farm": 50.0}, recipes(), 200.0), 1.0)

    def test_no_hands_hire_nothing(self):
        self.assertEqual(opening_own.hired_share({"farm": 5.0}, recipes(), 0.0), 0.0)


class IdleHoursTests(unittest.TestCase):
    def test_hours_neither_hired_nor_spent_on_household_work_are_idle(self):
        self.assertEqual(opening_own.idle_hours(1000.0, 0.25, 100.0), 650.0)

    def test_idle_hours_are_never_negative(self):
        self.assertEqual(opening_own.idle_hours(1000.0, 0.75, 400.0), 0.0)


class LessWhatItGrewTests(unittest.TestCase):
    def test_a_floor_half_grown_is_half_bought_and_its_budget_cut_to_match(self):
        basket = types.SimpleNamespace(needs=(types.SimpleNamespace(
            need_id="food", subsistence_per_person=1.0, goods=(("flour", 1.0),)),))
        cohort = types.SimpleNamespace(people=10.0)
        bid = Bid("household", "flour", "area", "tile", 10.0, 10.0, 1.0, 1.0, 100.0)
        cut = year_goods.less_what_it_grew(AgentOrders(bids=(bid,)), cohort, basket, {"food": 5.0}).bids[0]
        self.assertEqual((cut.floor_quantity, cut.flexible_quantity, cut.budget), (5.0, 10.0, 75.0))


class RestingPurseExtraSpendingTests(unittest.TestCase):
    def test_a_purse_for_spending_beyond_income_lets_the_rule_spend_exactly_that_much(self):
        purse = opening_resting.resting_household_purse(100.0, 0.0, extra_spending=30.0)
        self.assertAlmostEqual(households_buffer_stock.spending_budget(100.0, 100.0 + purse, 0.0), 130.0)


def mill_and_feeder():
    return {"mill": Recipe("mill", {"flour": 1000.0, "bran": 150.0}, {}, {"miller": 5.0}),
            "feed": Recipe("feed", {"lard": 10.0}, {"bran": 600.0}, {"herder": 1.0})}


class MainOutputsTests(unittest.TestCase):
    def test_the_output_worth_most_is_what_a_run_is_for(self):
        self.assertEqual(opening_runs.main_outputs(mill_and_feeder(), {"flour": 1.0, "bran": 0.5, "lard": 9.0}),
                         {"mill": "flour", "feed": "lard"})


class ByProductCeilingsTests(unittest.TestCase):
    def test_a_user_of_bran_runs_only_as_far_as_the_runs_for_flour_supply_it(self):
        recipes = mill_and_feeder()
        users = opening_runs.by_product_users(recipes, {"mill": "flour", "feed": "lard"})
        self.assertEqual(opening_runs.by_product_ceilings({"mill": 1.0}, recipes, users, {}), {"feed": 150.0 / 600.0})


class RequiredRunsByProductTests(unittest.TestCase):
    def test_bran_wanted_beyond_what_milling_for_flour_makes_does_not_add_runs_of_the_mill(self):
        recipes = mill_and_feeder()
        demand = {"town": {"flour": 1000.0, "lard": 10.0}}
        ranked = {"flour": ["mill"], "bran": ["mill"], "lard": ["feed"]}
        runs = opening_runs.required_runs(demand, ranked, recipes, None, None, {"mill": "flour", "feed": "lard"})
        self.assertEqual((round(runs["mill"], 9), round(runs["feed"], 9)), (1.0, 0.25))
