"""Things an actor will not do: the exclusion list the automatic starters honour (`excluded` of the seat's projects)."""
from . import exclusion_rules


class Exclusions:
	def exclusion_entry_known(self, entry):
		return exclusion_rules.entry_known(entry, self.needs.tree_nodes())

	def exclusion_reason(self, node_id):
		return exclusion_rules.reason(self.needs.legacy_projects().excluded, node_id, self.needs.tree_nodes())
