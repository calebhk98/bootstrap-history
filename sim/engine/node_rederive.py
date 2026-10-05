"""Keep the tree's derived revenue and upkeep at the techniques the civilisation holds now.

The figures are derived at the gate technologies held (`node_revenue.for_civilisation`, which caches
per held gate set); research that adds a gate changes what can be made and at what cost, so the Sim
re-derives when that set changes.
"""
from . import money_units, node_revenue, prices as price_solver
from .wage_schedule import build_schedule


def held_gate_set(held_techs):
    return frozenset(price_solver.all_gate_nodes()) & frozenset(held_techs)


class NodeRederiveMixin:

    def _remember_derived_gates(self, held_techs):
        self._derived_gate_set = held_gate_set(held_techs)

    def refresh_derived_nodes(self):
        """Re-derive node revenue and upkeep when the held gate technologies differ from the last derivation."""
        held = self.state.projects.done
        gates = held_gate_set(held)
        if gates == self._derived_gate_set:
            return
        from .data import TRADE_REGISTRY
        schedule = build_schedule(TRADE_REGISTRY, self.start_civ)
        derived = node_revenue.for_civilisation(self.nodes, self.start_civ, schedule, held_techs=held)
        money_units.price_nodes(derived.values(), schedule.wages_per_hour(), schedule.money_per_labour_hour)
        self.nodes = derived
        self._derived_gate_set = gates
        # revenue, upkeep and capability_factor memos were read from the old figures
        self._done_changed()
        self._operating_changed()
