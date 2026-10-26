"""Where the market ceiling's deduction falls.

Revenue passes through one saturating ceiling after the concerns are added up, so every earner is cut by the same share. The
ledger states the total cut; this attributes it to the categories (and the workshop) that suffer it, so the rows sum to that
total."""
from . import rules


class Absorption:

	def market_absorption_by_category(self, deduction):
		"""Rows {category, nominal, absorbed, lost, concerns} whose `lost` values add up to `deduction`, the figure the ledger
		deducts."""
		if deduction <= 0:
			return []
		nodes = self.needs.tree_nodes()
		workshop = self.needs.workshop_output() * self.needs.output_factor()
		return rules.absorption_by_category(deduction, self.needs.concern_market(), lambda node_id: nodes[node_id].get("cat"), workshop)
