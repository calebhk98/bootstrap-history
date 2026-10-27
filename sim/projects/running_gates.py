"""The works a node needs running: what is missing, the sentence that says so, and closing what relied on a lapsed work."""
from sim.refusal import Refusal
from sim.reporting.api import RecordEvent

from . import closure_reasons, running_gate_rules


class RunningGates:
	CLOSED_GATE_LAPSED = closure_reasons.CLOSED_GATE_LAPSED

	def _setup_running_gates(self) -> None:
		self._gate_index_cache = None             # (the tree it was built from, {work: ids that require it running})

	def _unmet_of(self, node):
		needs = self.needs
		return running_gate_rules.unmet_running_gates(node.get("requires_running"), needs.legacy_projects().done,
		                                              lambda work: needs.running[work])

	def _ways_short_of(self, node):
		return running_gate_rules.ways_short(node.get("requires_ways"), self._built_way_km)

	def unmet_running_gates(self, node_id):
		"""The works `node_id` requires running that are not, in the order the node lists them."""
		return self._unmet_of(self.needs.tree_nodes()[node_id])

	def ways_short(self, node_id):
		"""{way: kilometres still to build} of what `requires_ways` asks beyond what is built."""
		return self._ways_short_of(self.needs.tree_nodes()[node_id])

	def _built_way_km(self, way):
		"""Kilometres of `way` the acting seat's record of what is built holds."""
		return self.needs.built_way_km(way)

	def gate_blocked(self, node_id):
		"""Whether a work or a length of way the node requires is missing."""
		return bool(self.unmet_running_gates(node_id) or self.ways_short(node_id))

	def running_gate_text(self, unmet, ways_short=None):
		"""What to tell a player whose start or opening waits on works that are not running."""
		held = self.needs.techniques_held()
		return running_gate_rules.gate_text(unmet, ways_short, self.needs.visible_to_player, lambda work: work in held)

	def running_gate_refusal(self, node_id):
		"""The sentence refusing to open `node_id` while a work it needs is not running, else None."""
		unmet, short = self.unmet_running_gates(node_id), self.ways_short(node_id)
		if not (unmet or short):
			return None
		return self._gate_refusal(unmet, short)

	def _gate_refusal(self, unmet, short):
		return Refusal("running_gate", self.running_gate_text(unmet, short), unmet=list(unmet), ways_short=dict(short))

	def _check_running_gates(self, node_id, node, ignore_trade, memo, why):
		"""Refuse a node whose required works are not running; the refusal names the remedy."""
		unmet, short = self._unmet_of(node), self._ways_short_of(node)
		if not (unmet or short):
			return None
		return False, (self._gate_refusal(unmet, short) if why else None)

	def _running_gate_index(self):
		"""({work id: sorted ids that require it running}, ids that require something), per tree."""
		nodes = self.needs.tree_nodes()
		cached = self._gate_index_cache
		if cached is not None and cached[0] is nodes:
			return cached[1]
		dependents = running_gate_rules.dependents_index(nodes)
		self._gate_index_cache = (nodes, dependents)
		return dependents

	def relied_on_running(self, node_id):
		"""Whether some node requires this one running."""
		return node_id in self._running_gate_index()

	def close_lapsed_dependents(self, year):
		"""Close every open node whose required work is no longer running, down the chain.
		Returns the ids closed, in the order they closed."""
		needs = self.needs
		dependents = self._running_gate_index()
		closed = []
		while True:
			lapsed = running_gate_rules.lapsed_dependents(dependents, needs.operating(), self.unmet_running_gates)
			if not lapsed:
				return closed
			node_id = lapsed[0]
			unmet = self.unmet_running_gates(node_id)
			needs.send(RecordEvent.of("work_closed_gate_lapsed", "%s closed: the work it needs running (%s) has stopped"
			                          % (node_id, ", ".join(unmet)), work=node_id, gates=list(unmet)))
			self.close_work(node_id, self.CLOSED_GATE_LAPSED, year, cascade=False)
			closed.append(node_id)
