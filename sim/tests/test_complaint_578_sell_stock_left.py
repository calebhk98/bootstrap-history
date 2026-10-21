"""Complaints/578: `sell` reports the holding the next sale draws on, and refuses a sale of more than is held.
The rules are sim/engine/sale_orders.py, called on built numbers; the command reading the same limits is the scenario in
test_scenarios_batch3."""
QUICK_TOPIC = True

import unittest

from sim.engine import sale_orders
from sim.refusal import cause_of, facts_of


class TonnesSoldTests(unittest.TestCase):
    def test_an_order_within_the_holding_and_the_market_sells_whole(self):
        self.assertEqual(sale_orders.tonnes_sold(100.0, 500.0, 300.0), 100.0)

    def test_an_order_is_cut_to_what_the_market_still_takes(self):
        self.assertEqual(sale_orders.tonnes_sold(400.0, 500.0, 120.0), 120.0)

    def test_an_order_is_cut_to_what_is_held(self):
        self.assertEqual(sale_orders.tonnes_sold(400.0, 90.0, 300.0), 90.0)


class AsksMoreThanHeldTests(unittest.TestCase):
    def test_more_than_is_held_is_asking_too_much(self):
        self.assertTrue(sale_orders.asks_more_than_held(100000.0, 2600.0))

    def test_exactly_the_holding_is_not(self):
        self.assertFalse(sale_orders.asks_more_than_held(2600.0, 2600.0))

    def test_float_noise_above_the_holding_is_not(self):
        self.assertFalse(sale_orders.asks_more_than_held(2600.0 + 1e-12, 2600.0))


class RefusalTests(unittest.TestCase):
    def test_not_enough_held_has_its_cause_and_states_the_quantity_held(self):
        refusal = sale_orders.not_enough_held_refusal("iron", 2600.0, 100000.0)
        self.assertEqual(cause_of(refusal), "not_enough_held")
        self.assertEqual(facts_of(refusal)["held_tonnes"], 2600.0)
        self.assertEqual(facts_of(refusal)["asked_tonnes"], 100000.0)
        self.assertEqual(facts_of(refusal)["material"], "iron")

    def test_market_full_has_its_cause_and_the_room(self):
        refusal = sale_orders.market_full_refusal("iron", 2600.0, 0.0)
        self.assertEqual(cause_of(refusal), "market_full")
        self.assertEqual(facts_of(refusal)["market_room_tonnes"], 0.0)


class SaleReplyTests(unittest.TestCase):
    def test_the_reply_reports_the_holding_and_room_the_next_sale_draws_on(self):
        reply = sale_orders.sale_reply("iron", 400.0, 450.0, held_after=2600.0, room_after=150.0, capital=1234.56)
        self.assertEqual((reply["stock_on_hand_tonnes"], reply["market_will_still_take_tonnes"]), (2600.0, 150.0))
        self.assertEqual((reply["sold_tonnes"], reply["asked_tonnes"]), (400.0, 450.0))
        self.assertEqual(reply["capital"], 1234.6)
        self.assertTrue(reply["ok"])


if __name__ == "__main__":
    unittest.main()
