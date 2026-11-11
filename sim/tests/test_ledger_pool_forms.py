"""A commodity pool's stock is held by material key and read as the pool total where any form will do (Complaint 977, stages 1
and 2): `ledger.pool_rules`."""
QUICK_TOPIC = True

import json
import unittest

from sim.ledger import pool_rules
from sim.ledger.rules import StockLedger, settled_stock

COMMODITIES = {"iron": {"material_keys": ["iron_bar_kg", "iron_ore_kg", "iron_bloom_kg"], "raised_material": "iron_ore_kg"},
               "coal": {"material_keys": ["coal_kg"]},
               "gold": {"material_keys": ["gold_kg", "gold_g"], "price_material": "gold_kg"}}


class PoolTotalTests(unittest.TestCase):
    def test_the_total_sums_every_form_and_anything_under_the_pool_id(self):
        stock = {"iron_bar_kg": 2.0, "iron_ore_kg": 5.0, "iron": 0.5, "coal_kg": 9.0}
        self.assertEqual(pool_rules.pool_total(stock, "iron", COMMODITIES), 7.5)

    def test_a_commodity_with_no_record_is_the_key_itself(self):
        self.assertEqual(pool_rules.pool_total({"sheep": 3.0, "iron": 1.0}, "sheep", COMMODITIES), 3.0)

    def test_nothing_held_is_zero(self):
        self.assertEqual(pool_rules.pool_total({}, "iron", COMMODITIES), 0.0)

    def test_held_by_form_lists_the_forms_held_in_key_order(self):
        stock = {"iron_ore_kg": 5.0, "iron_bar_kg": 2.0, "coal_kg": 1.0}
        self.assertEqual(list(pool_rules.held_by_form(stock, "iron", COMMODITIES).items()),
                         [("iron_bar_kg", 2.0), ("iron_ore_kg", 5.0)])


class WriterTests(unittest.TestCase):
    def test_a_bar_purchase_is_held_under_the_bar_key(self):
        self.assertEqual(pool_rules.form_key("iron_bar_kg", "iron", COMMODITIES), "iron_bar_kg")
        stock = {}
        pool_rules.change_tonnes(stock, {}, "iron_bar_kg", 3.0)
        self.assertEqual(stock, {"iron_bar_kg": 3.0})

    def test_a_material_the_pool_does_not_name_is_held_under_the_pool_id(self):
        self.assertEqual(pool_rules.form_key("iron_wire_kg", "iron", COMMODITIES), "iron")

    def test_the_mines_flow_is_held_under_the_form_they_raise(self):
        self.assertEqual(pool_rules.raised_key("iron", COMMODITIES), "iron_ore_kg")
        self.assertEqual(pool_rules.raised_key("coal", COMMODITIES), "coal")

    def test_a_pool_with_no_distinct_raised_form_banks_its_mines_as_the_form_it_is_priced_as(self):
        # so a bill for that form (held under its own key) is met by the pool's mines
        self.assertEqual(pool_rules.raised_key("gold", COMMODITIES), "gold_kg")
        self.assertEqual(pool_rules.raised_key("gold", COMMODITIES), pool_rules.form_key("gold_kg", "gold", COMMODITIES))

    def test_banking_sets_exactly_the_key_and_leaves_the_other_forms(self):
        stock = {"iron_bar_kg": 2.0, "iron_ore_kg": 1.0}
        pool_rules.bank_tonnes(stock, "iron_ore_kg", 4.0)
        self.assertEqual(stock, {"iron_bar_kg": 2.0, "iron_ore_kg": 4.0})

    def test_a_sale_beyond_the_sold_form_touches_only_that_form(self):
        stock, opening = {"iron_bar_kg": 2.0, "iron_ore_kg": 1.0}, {}
        self.assertFalse(pool_rules.held_enough(stock, "iron_ore_kg", -2.5))
        self.assertTrue(pool_rules.held_enough(stock, "iron_ore_kg", -1.0))
        pool_rules.change_tonnes(stock, opening, "iron_ore_kg", -1.0)
        self.assertEqual(stock, {"iron_bar_kg": 2.0, "iron_ore_kg": 0.0})
        self.assertEqual(opening, {"iron_ore_kg": -1.0})

    def test_a_taking_from_a_form_never_held_is_not_enough(self):
        self.assertFalse(pool_rules.held_enough({}, "iron_bar_kg", -0.5))
        self.assertTrue(pool_rules.held_enough({}, "iron_bar_kg", 0.5))


class SaveRoundTripTests(unittest.TestCase):
    def test_a_ledger_holding_two_forms_round_trips_as_a_plain_dict(self):
        ledger = StockLedger({"iron_ore_kg": 4.0, "iron_bar_kg": 2.0})
        reloaded = settled_stock(json.loads(json.dumps(dict(ledger))), {})
        self.assertEqual(dict(reloaded), {"iron_ore_kg": 4.0, "iron_bar_kg": 2.0})
        self.assertEqual(pool_rules.pool_total(reloaded, "iron", COMMODITIES), 6.0)


if __name__ == "__main__":
    unittest.main()
