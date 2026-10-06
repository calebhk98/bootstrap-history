"""The last sliver of a project's bill.

Prices move after a bill is frozen and instalments round, so a finished project
can be left owing a few cash units. Making it wait a whole extra year for that
is a bookkeeping artefact, so the sliver is paid at the final scheduled payment.
"""
from sim.constants import declare
from sim.agents.api import edges


class ProjectCostTailMixin:

    COST_TAIL_SETTLE_SHARE = declare(
        "COST_TAIL_SETTLE_SHARE", 0.001, kind="temporary_heuristic",
        unit="fraction of the project's bill", source=None, confidence="D",
        why="How small a remainder, after the work and the calendar floor are "
            "done, counts as rounding and is paid at once rather than waiting "
            "a further year. Tuned, not measured.")

    def settle_cost_tail(self, node_id, project_state):
        """Pay a rounding-sized remainder of the bill now. Returns the amount."""
        tail = project_state["cost_left"]
        if tail <= 0.5 or project_state.get("underfunded_this_year"):
            return 0.0
        if tail > self.COST_TAIL_SETTLE_SHARE * self.project_cost(node_id):
            return 0.0
        household = self.state.household
        self.pay_edge(edges.EDGE_SUPPLIERS, tail, "project payments")
        household.total_spend += tail
        project_state["spent"] += tail
        project_state["cost_left"] = 0.0
        return tail
