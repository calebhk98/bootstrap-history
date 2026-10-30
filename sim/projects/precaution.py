"""Paying more to lower a project's chance of failing: what a node's pilot plant or redundant team costs and buys (the
kinds and the figures are in precaution_rules.py)."""
from . import precaution_rules


class Precaution:
	def precaution_spec(self, node_id):
		"""The node's resolved precaution (label and the three figures), or None."""
		return precaution_rules.resolve(self.needs.mechanic["precaution"].get(node_id))

	def precaution_chosen(self, node_id):
		"""True when the running project for this node bought the precaution."""
		return bool((self.seat.active.get(node_id) or {}).get("precaution"))

	def precaution_relief(self, node_id, bought):
		return precaution_rules.relief_multiplier(self.precaution_spec(node_id), bought)

	def precaution_extra_cost(self, node_id, bill):
		return precaution_rules.extra_cost(self.precaution_spec(node_id), bill)

	def precaution_extra_hours(self, node_id):
		return precaution_rules.extra_hours(self.precaution_spec(node_id), self.needs.tree_nodes()[node_id]["ph"],
		                                    self.rebuild_work_factor(node_id))

	def precaution_quote(self, node_id):
		"""What the node's pilot plant or redundant team would cost and buy, or None."""
		spec = self.precaution_spec(node_id)
		if spec is None:
			return None
		return precaution_rules.quote(
			spec, self.needs.project_cost(node_id), self.needs.tree_nodes()[node_id]["ph"], self.rebuild_work_factor(node_id),
			self.effective_risk(node_id, precaution=False), self.effective_risk(node_id, precaution=True))
