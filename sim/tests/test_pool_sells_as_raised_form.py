"""A sale is priced and cleared as the form the seat sells, never as a dearer form of the pool (Complaint 576, refined by 977 stage 4):
mined ore cannot sell at the bar price, and bar the seat bought cannot sell as ore. `prices.rules.sold_material` / `sale_forms`."""
QUICK_TOPIC = True

import unittest

from sim.prices.rules import priced_key, sale_forms, sold_material

IRON = {"material_keys": ["iron_bar_kg", "iron_ore_kg"], "price_material": "iron_bar_kg", "raised_material": "iron_ore_kg"}
COAL = {"material_keys": ["coal_kg"], "price_material": "coal_kg"}
PRICES = {"iron_bar_kg": 1.5, "iron_ore_kg": 0.015, "coal_kg": 0.02}


class SoldMaterialTests(unittest.TestCase):
    def test_the_pool_holding_only_mined_ore_sells_as_the_ore_not_the_bar_it_is_priced_as(self):
        sold = sold_material("iron", "iron", IRON, {"iron_ore_kg": 4.0})
        self.assertEqual(sold, "iron_ore_kg")
        self.assertNotEqual(sold, priced_key("iron", PRICES, IRON))

    def test_the_pool_holding_nothing_sells_as_the_form_its_mines_raise(self):
        self.assertEqual(sold_material("iron", "iron", IRON, {}), "iron_ore_kg")

    def test_the_ore_good_is_far_cheaper_than_the_pool_priced_good(self):
        sold = sold_material("iron", "iron", IRON, {"iron_ore_kg": 4.0})
        self.assertLess(PRICES[priced_key(sold, PRICES, IRON)], PRICES[priced_key("iron", PRICES, IRON)] / 10)

    def test_bar_the_seat_bought_sells_as_bar_when_it_is_named(self):
        self.assertEqual(sold_material("iron_bar_kg", "iron", IRON, {"iron_bar_kg": 3.0}), "iron_bar_kg")
        self.assertEqual(PRICES[priced_key("iron_bar_kg", PRICES, IRON)], 1.5)

    def test_ore_sells_as_ore_when_it_is_named_even_with_bar_held(self):
        self.assertEqual(sold_material("iron_ore_kg", "iron", IRON, {"iron_bar_kg": 3.0, "iron_ore_kg": 1.0}), "iron_ore_kg")

    def test_the_pool_name_with_bar_and_ore_held_offers_the_raised_form_first_then_the_rest(self):
        self.assertEqual(sale_forms("iron", "iron", IRON, {"iron_bar_kg": 3.0, "iron_ore_kg": 1.0}), ["iron_ore_kg", "iron_bar_kg"])

    def test_the_pool_name_with_only_bar_held_sells_the_bar(self):
        self.assertEqual(sale_forms("iron", "iron", IRON, {"iron_bar_kg": 3.0}), ["iron_bar_kg"])

    def test_a_seat_holding_bar_it_bought_and_ore_it_mined_sells_each_at_its_own_goods_price(self):
        forms = sale_forms("iron", "iron", IRON, {"iron_bar_kg": 3.0, "iron_ore_kg": 1.0})
        self.assertEqual({form: PRICES[priced_key(form, PRICES, IRON)] for form in forms}, {"iron_bar_kg": 1.5, "iron_ore_kg": 0.015})

    def test_a_form_held_at_zero_is_not_offered(self):
        self.assertEqual(sale_forms("iron", "iron", IRON, {"iron_bar_kg": 0.0, "iron_ore_kg": 2.0}), ["iron_ore_kg"])

    def test_a_material_the_pool_does_not_name_sells_as_itself(self):
        self.assertEqual(sold_material("iron_wire_kg", "iron", IRON, {"iron_ore_kg": 2.0}), "iron_wire_kg")

    def test_a_commodity_with_no_distinct_raised_form_sells_as_itself(self):
        self.assertEqual(sold_material("coal_kg", "coal", COAL, {"coal_kg": 1.0}), "coal_kg")
        self.assertEqual(sold_material("coal", "coal", COAL, {"coal_kg": 1.0}), "coal_kg")


if __name__ == "__main__":
    unittest.main()
