"""`Categories.goods_categories`: the categories of the tree's nodes whose traits flag a shared market, read from the category traits."""
QUICK_TOPIC = True

import unittest

from sim.markets.category_views import SHARED_MARKET, Categories
from sim.tests import module_harness

NODES = {"loom": {"cat": "weaving"}, "press": {"cat": "printing_shop"}, "school": {"cat": "teaching"}, "bare": {}}
TRAITS = {("weaving", SHARED_MARKET): True, ("printing_shop", SHARED_MARKET): True}


def categories_over(nodes=NODES):
	return module_harness.part(Categories, views={
		"tree_nodes": lambda: nodes, "category_trait": lambda category, trait: TRAITS.get((category, trait), False)})


class GoodsCategories(unittest.TestCase):
	def test_the_categories_are_those_of_nodes_flagged_with_the_shared_market_trait(self):
		self.assertEqual(categories_over().goods_categories(), frozenset({"weaving", "printing_shop"}))

	def test_a_node_with_no_category_adds_none(self):
		self.assertEqual(categories_over({"bare": {}}).goods_categories(), frozenset())

	def test_the_real_traits_flag_the_consumer_categories(self):
		from sim.knowledge import category_traits
		catalogue = category_traits.load("/nonexistent")
		flagged = {category for category in catalogue["categories"] if category_traits.has_trait(catalogue, category, SHARED_MARKET)}
		self.assertIn("textiles", flagged)
		self.assertNotIn("measurement", flagged)


if __name__ == "__main__":
	unittest.main()
