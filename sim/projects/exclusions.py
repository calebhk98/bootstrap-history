"""Things an actor will not do: the exclusion list the automatic starters honour (`excluded` of the seat's projects)."""
from . import exclusion_rules


class Exclusions:
	def exclusion_entry_known(self, entry):
		return exclusion_rules.entry_known(entry, self.needs.tree_nodes())

	def exclusion_reason(self, node_id):
		return exclusion_rules.reason(self.seat.excluded, node_id, self.needs.tree_nodes())

	def exclusions(self):
		"""The acting seat's exclusion list (the live set)."""
		return self.seat.excluded

	def apply_exclude(self, command):
		self.seat.excluded.add(command.entry)

	def apply_include(self, command):
		if command.entry is None:
			self.seat.excluded.clear()
			return True
		if command.entry not in self.seat.excluded:
			return False
		self.seat.excluded.discard(command.entry)
		return True

	def keep_staffed(self):
		"""The concerns flagged to be hired for each year before the closure rule (the live set)."""
		return self.seat.keep_staffed

	def apply_keep_staffed(self, command):
		if command.kept:
			self.seat.keep_staffed.add(command.node_id)
		else:
			self.seat.keep_staffed.discard(command.node_id)
