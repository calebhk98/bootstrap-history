"""The last sliver of a project's bill.

Prices move after a bill is frozen and instalments round, so a finished project can be left owing a few cash units.
Making it wait a whole extra year for that is a bookkeeping artefact, so the sliver is paid at the final scheduled
payment."""
from sim.agents.api import edges
from sim.ledger.api import NoteSpend, PayEdge

from .constants import COST_TAIL_SETTLE_SHARE


class CostTail:
	def settle_cost_tail(self, node_id, project_state):
		"""Pay a rounding-sized remainder of the bill now. Returns the amount."""
		tail = project_state["cost_left"]
		if tail <= 0.5 or project_state.get("underfunded_this_year"):
			return 0.0
		if tail > COST_TAIL_SETTLE_SHARE * self.needs.project_cost(node_id):
			return 0.0
		self.needs.send(PayEdge(edges.EDGE_SUPPLIERS, tail, "project payments"))
		self.needs.send(NoteSpend(tail))
		project_state["spent"] += tail
		project_state["cost_left"] = 0.0
		return tail
