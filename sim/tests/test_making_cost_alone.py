"""making_cost_alone: a good made only beside other outputs has no making cost of its own."""

QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.economy.making_cost_alone import costs_of_goods_made_alone, goods_made_alone, no_cost, the_price_it_had

RECIPES = {
    "grow_millet": SimpleNamespace(outputs={"millet_kg": 100.0}),
    "keep_pigs": SimpleNamespace(outputs={"meat_kg": 70.0, "lard_kg": 30.0}),
    "hunt": SimpleNamespace(outputs={"meat_kg": 5.0}),
    "mill": SimpleNamespace(outputs={"flour_kg": 80.0, "bran_kg": 20.0}),
}


class GoodsMadeAlone(unittest.TestCase):
    def test_the_only_output_of_some_recipe_is_made_alone(self):
        self.assertEqual(goods_made_alone(RECIPES), frozenset({"millet_kg", "meat_kg"}))

    def test_no_recipes_make_nothing_alone(self):
        self.assertEqual(goods_made_alone({}), frozenset())


class CostsOfGoodsMadeAlone(unittest.TestCase):
    COSTS = {"millet_kg": 0.2, "meat_kg": 1.5, "lard_kg": 0.9, "flour_kg": 0.6, "bran_kg": 0.05}

    def test_a_joint_product_no_recipe_makes_alone_has_no_cost(self):
        self.assertEqual(costs_of_goods_made_alone(self.COSTS, RECIPES), {"millet_kg": 0.2, "meat_kg": 1.5})

    def test_the_costs_given_are_not_changed(self):
        before = dict(self.COSTS)
        costs_of_goods_made_alone(self.COSTS, RECIPES)
        self.assertEqual(self.COSTS, before)

    def test_a_good_with_no_cost_stays_without_one(self):
        self.assertEqual(costs_of_goods_made_alone({"lard_kg": 0.9}, RECIPES), {})


class WhatACostlessMarketPlansFrom(unittest.TestCase):
    def test_under_the_search_rules_nothing(self):
        self.assertIsNone(no_cost(2.5))
        self.assertIsNone(no_cost(None))

    def test_under_the_clearing_rules_the_price_it_had(self):
        self.assertEqual(the_price_it_had(2.5), 2.5)
        self.assertIsNone(the_price_it_had(None))


if __name__ == "__main__":
    unittest.main()
