"""What a forgotten technology still has going for it when it is rebuilt (the shares are in rebuild_rules.py)."""
from sim.knowledge.api import CORPUS_HEDGE_LOSS_CHANCE_NONE

from . import rebuild_rules
from .constants import REBUILD_RETAINED_CEILING


class Rebuild:
	def _setup_rebuild(self) -> None:
		self._dependents_cache = None             # (the tree it was built from, the index): rebuilt when the tree is replaced

	def _dependents_index(self):
		"""{node id: ids of nodes listing it as a prerequisite}, built once per tree."""
		nodes = self.needs.tree_nodes()
		cached = self._dependents_cache
		if cached is not None and cached[0] is nodes:
			return cached[1]
		index = rebuild_rules.dependents_index(nodes)
		self._dependents_cache = (nodes, index)
		return index

	def is_being_rebuilt(self, node_id):
		"""Whether `node_id` was built once, was lost, and is not held now."""
		return node_id in (self.needs.techniques_forgotten() or {}) and node_id not in self.needs.techniques_held()

	def rebuild_survivals(self, node_id):
		"""{what survives: share 0..1} for a forgotten node, from current state: `copy` the record held beyond one
		site, `practice` the share of its trades still worked by people you keep, `plant` the share of what was built
		on it that still stands."""
		node = self.needs.tree_nodes()[node_id]
		chance, _fraction, _hedge = self.needs.corpus_hedge()
		copy = rebuild_rules.copy_share(CORPUS_HEDGE_LOSS_CHANCE_NONE, chance)
		practice = rebuild_rules.practice_share(list(node["lab"]), self.needs.staff()["employees"])
		plant = rebuild_rules.plant_share(self._dependents_index().get(node_id, []), self.needs.techniques_held())
		return {"copy": copy, "practice": practice, "plant": plant}

	def rebuild_retained_share(self, node_id):
		"""The share of the original work a rebuild skips; zero for a node that was never lost."""
		if not self.is_being_rebuilt(node_id):
			return 0.0
		return rebuild_rules.retained_share(self.rebuild_survivals(node_id), REBUILD_RETAINED_CEILING)

	def rebuild_work_factor(self, node_id):
		"""What is left to do, as a fraction of a first build: frozen at the start of a running project, live before it."""
		record = self.seat.active.get(node_id)
		if record is not None and "rebuild_factor" in record:
			return record["rebuild_factor"]
		return 1.0 - self.rebuild_retained_share(node_id)

	def rebuild_explanation(self, node_id):
		"""One line for `why` on a lost node: what a rebuild keeps and why, or None."""
		if not self.is_being_rebuilt(node_id):
			return None
		return rebuild_rules.explanation(self.needs.techniques_forgotten()[node_id], self.rebuild_survivals(node_id),
		                                 self.rebuild_retained_share(node_id))
