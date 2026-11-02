"""Complaints/578: `sell` refuses a sale of more than is held.
The rules are sim/engine/sale_orders.py, called on built numbers; the command reading the same limits is the scenario in
test_scenarios_batch3."""
QUICK_TOPIC = True

import unittest

from sim.engine import sale_orders
from sim.refusal import cause_of, facts_of


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


if __name__ == "__main__":
    unittest.main()
