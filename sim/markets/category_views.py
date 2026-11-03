from sim.assembly.api import Part
"""The goods categories: which tree nodes sell into each."""


class Categories(Part):

	def __init__(self, module):
		super().__init__(module)
		self._nodes_by_category = None     # category -> node ids, in the tree's order; the tree does not change after load

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
