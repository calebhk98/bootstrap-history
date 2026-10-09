"""A plough crop holds a team of draught animals as plant and grazes it on land; a society without draught
animals grows the same crop by hand (Complaint 398, folded in from 395)."""

QUICK_TOPIC = True

import unittest

from sim.economy.households_own import own_production_options
from sim.economy.recipes import recipes_from_production_data
from sim.economy.types import Recipe
from sim.engine.economy_port_setup import allowed_entries
from sim.tests import economy_fixture as fixture
from sim.world import demand


class RealWheatDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.production = demand.production_data()
        cls.recipes = recipes_from_production_data(cls.production)

    def test_the_plough_recipe_holds_a_team_as_plant_and_grazes_it(self):
        plough, hand = self.recipes["wheat_kg"], self.recipes["wheat_hoe_kg"]
        self.assertGreater(plough.plant_goods.get("draught_animal_kg", 0.0), 0.0)
        self.assertGreater(plough.plant_life_years, 0.0)
        self.assertEqual(plough.inputs, {})
        self.assertGreater(self.production["wheat_kg"]["land_hectare_years"],
                           self.production["wheat_hoe_kg"]["land_hectare_years"])
        self.assertLess(plough.labour_hours["labourer"], hand.labour_hours["labourer"])

    def test_the_hand_recipe_needs_no_team(self):
        hand = self.recipes["wheat_hoe_kg"]
        self.assertEqual((hand.plant_goods, hand.inputs), ({}, {}))
        self.assertEqual(hand.outputs, self.recipes["wheat_kg"].outputs)

    def test_a_society_that_cannot_keep_draught_animals_is_left_with_the_hand_recipe(self):
        allowed = allowed_entries(self.production, {"some_other_node"})
        self.assertIn("wheat_hoe_kg", allowed)
        self.assertNotIn("wheat_kg", allowed)
        with_animals = allowed_entries(self.production, {self.production["wheat_kg"]["requires_node"]})
        self.assertIn("wheat_kg", with_animals)


class OwnPlotTests(unittest.TestCase):
    def test_a_household_grows_a_crop_with_its_own_team_but_not_one_that_needs_bought_inputs(self):
        basket = fixture.basket()
        good = next(each.goods[0][0] for each in basket.needs if each.goods)
        recipes = {"plough": Recipe("plough", {good: 10.0}, {}, {"labourer": 5.0}, {"draught_animal_kg": 1.0}, {}, 10.0),
                   "bought": Recipe("bought", {good: 10.0}, {"fuel": 1.0}, {"labourer": 5.0})}
        options = own_production_options(recipes, {"plough": 1.0, "bought": 1.0}, basket)
        recipe_ids = {row[1] for rows in options.values() for row in rows}
        self.assertIn("plough", recipe_ids)
        self.assertNotIn("bought", recipe_ids)


if __name__ == "__main__":
    unittest.main()
