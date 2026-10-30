"""Goods that serve the same household need substitute for one another: rules over the need data's goods table."""

QUICK_TOPIC = True

import unittest

from sim.markets import need_substitutes

GOODS = {"wheat_kg": {"satisfies": {"food": 1.0}}, "maize_kg": {"satisfies": {"food": 0.9}},
         "wool_kg": {"satisfies": {"warmth": 1.0, "clothing": 1.0}}, "flax_kg": {"satisfies": {"clothing": 0.8}},
         "salt_kg": {}}


class NeedSubstitutes(unittest.TestCase):
	def setUp(self):
		self.served = need_substitutes.needs_served(GOODS)

	def test_the_needs_a_material_serves_are_listed(self):
		self.assertEqual(self.served["wool_kg"], frozenset({"warmth", "clothing"}))
		self.assertEqual(self.served["salt_kg"], frozenset())

	def test_goods_that_serve_the_same_need_are_substitutes(self):
		self.assertEqual(need_substitutes.substitutes_of(self.served, "wheat_kg"), frozenset({"maize_kg"}))
		self.assertEqual(need_substitutes.substitutes_of(self.served, "wool_kg"), frozenset({"flax_kg"}))

	def test_a_good_is_not_its_own_substitute(self):
		self.assertNotIn("wheat_kg", need_substitutes.substitutes_of(self.served, "wheat_kg"))

	def test_a_good_no_need_names_has_no_substitutes(self):
		self.assertEqual(need_substitutes.substitutes_of(self.served, "nothing_at_all"), frozenset())
		self.assertEqual(need_substitutes.substitutes_of(self.served, "salt_kg"), frozenset())

	def test_the_goods_that_serve_one_need_are_listed(self):
		self.assertEqual(need_substitutes.serving(self.served, "food"), frozenset({"wheat_kg", "maize_kg"}))
		self.assertEqual(need_substitutes.serving(self.served, "shelter"), frozenset())

	def test_a_good_serves_a_need_only_when_the_data_names_one(self):
		self.assertTrue(need_substitutes.serves_a_need(self.served, "flax_kg"))
		self.assertFalse(need_substitutes.serves_a_need(self.served, "salt_kg"))
		self.assertFalse(need_substitutes.serves_a_need(self.served, "nothing_at_all"))


if __name__ == "__main__":
	unittest.main()
