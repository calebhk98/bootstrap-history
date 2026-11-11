"""A tonne of a commodity pool a mine raised sells as the form the mine raises, not as the worked form the pool is priced as
(Complaint 576): `prices.rules.sold_material`."""
QUICK_TOPIC = True

import unittest

from sim.prices.rules import priced_key, sold_material

IRON = {"material_keys": ["iron_bar_kg", "iron_ore_kg"], "price_material": "iron_bar_kg", "raised_material": "iron_ore_kg"}
COAL = {"material_keys": ["coal_kg"], "price_material": "coal_kg"}
PRICES = {"iron_bar_kg": 1.5, "iron_ore_kg": 0.015, "coal_kg": 0.02}


class SoldMaterialTests(unittest.TestCase):
    def test_the_pool_priced_as_bar_sells_as_the_ore_its_mines_raise(self):
        self.assertEqual(sold_material("iron", IRON), "iron_ore_kg")
        self.assertEqual(sold_material("iron_bar_kg", IRON), "iron_ore_kg")

    def test_the_ore_good_is_far_cheaper_than_the_pool_priced_good(self):
        sold = sold_material("iron", IRON)
        self.assertNotEqual(sold, priced_key("iron", PRICES, IRON))
        self.assertLess(PRICES[priced_key(sold, PRICES, IRON)], PRICES[priced_key("iron", PRICES, IRON)] / 10)

    def test_a_commodity_with_no_distinct_raised_form_sells_as_itself(self):
        self.assertEqual(sold_material("coal_kg", COAL), "coal_kg")
