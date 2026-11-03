"""The goods categories: which tree nodes sell into each."""
from sim.assembly.api import Part

SHARED_MARKET = "shared_market"   # the category trait (data/world/category_traits.json) of a goods category


class Categories(Part):

	def __init__(self, module):
		super().__init__(module)
		self._nodes_by_category = None     # category -> node ids, in the tree's order; the tree does not change after load
		self._goods_categories = None      # the categories with the shared-market trait; likewise

	def goods_categories(self):
		"""The goods categories: the categories of the tree's nodes whose traits say their concerns share one market."""
		found = self._goods_categories
		if found is None:
			found = self._goods_categories = frozenset(
				node["cat"] for node in self.needs.tree_nodes().values()
				if node.get("cat") and self.needs.category_trait(node["cat"], SHARED_MARKET))
		return found

	def nodes_in_category(self, category):
		"""Every node key that carries this goods category, in the tree's own order (never changing after load)."""
		cache = self._nodes_by_category
		if cache is None:
			cache = {}
			for node_id, node in self.needs.tree_nodes().items():
				node_category = node.get("cat")
				if node_category:
					cache.setdefault(node_category, []).append(node_id)
			self._nodes_by_category = cache
		return cache.get(category, ())
