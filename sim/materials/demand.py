"""What the seat's work draws: the tonnes a year its projects and finished installations need, and the tables that hold
while they are unchanged."""
import collections
from typing import Any, Dict, List, Tuple

from . import rules
from .readings import Readings


class Demand:
    """Needs: active_project_ids, active_projects_version, techniques_version, tree_nodes, techniques_held."""

    @property
    def readings(self) -> Readings:
        """What is remembered for the acting seat."""
        seat_id = self.clock.acting_seat
        readings = self._readings.get(seat_id)
        if readings is None:
            readings = self._readings[seat_id] = Readings()
        return readings

    def chosen_fuel(self, node_id: str) -> str:
        """Which fuel the node burns given the techniques held: "coke" when the best fuel option it names is coke or coal."""
        tree = self.needs.tree_nodes()
        done = self.needs.techniques_held()
        return rules.fuel_choice(tree[node_id].get("req_any"), lambda option: option in done or option not in tree)

    def uses_coke(self, node_id: str) -> bool:
        return self.chosen_fuel(node_id) == "coke"

    def done_in_order(self) -> List[str]:
        """Everything the seat holds, in the tree's own order (float sums over it must not depend on hash order)."""
        done = self.needs.techniques_held()
        return [node_id for node_id in self.needs.tree_nodes() if node_id in done]

    def standing_terms(self) -> List[Tuple[str, float]]:
        """(material, tonnes a year) for every finished installation that keeps drawing material, in done order; depends
        only on what is done."""
        done = self.needs.techniques_held()
        version = self.needs.techniques_version()
        cached = self._standing
        if cached is not None and cached[0] == version and cached[1] is done:
            return cached[2]
        terms = rules.standing_terms(self.done_in_order(), self.needs.tree_nodes(), self.uses_coke)
        self._standing = (version, done, terms)
        return terms

    def annual_material_demand(self) -> collections.Counter:
        """Tonnes a year of the materials that bind, from the work in hand (a copy)."""
        readings = self.readings
        versions = (self.needs.active_projects_version(), self.needs.techniques_version())
        cache = readings.annual
        if cache is not None and cache[0] == versions:
            return cache[1].copy()
        # progress on a project bumps the active version without changing which projects are active; the demand depends
        # only on which are active
        active_keys = tuple(self.needs.active_project_ids())
        keyed = self._annual_keys
        if cache is not None and keyed is not None and keyed[0] == active_keys and keyed[1] == versions[1]:
            readings.annual = (versions, cache[1])
            return cache[1].copy()
        demand = rules.annual_demand(active_keys, self.needs.tree_nodes(), self.uses_coke, self.standing_terms())
        readings.annual = (versions, demand)
        self._annual_keys = (active_keys, versions[1])
        return demand.copy()

    def cached_demand(self) -> Any:
        """The demand the last throttle saw, else the demand now."""
        held = self.readings.held
        return held if held is not None else self.annual_material_demand()

    def demand_held(self) -> Any:
        """The demand the last throttle saw (the object itself, for identity comparisons), or None."""
        return self.readings.held

    def demand_by_tag(self) -> collections.Counter:
        """`cached_demand` grouped by the pool it draws on, worked out once per demand."""
        demand = self.cached_demand()
        cached = self.readings.by_tag
        if cached is not None and cached[0] is demand:
            return cached[1]
        by_tag = self.demand_by_supply_tag(demand)
        self.readings.by_tag = (demand, by_tag)
        return by_tag

    def demand_by_commodity(self) -> Dict[str, List[Tuple[str, float]]]:
        """`demand_by_tag` grouped by commodity, worked out once per demand."""
        demand = self.cached_demand()
        cached = self.readings.by_commodity
        if cached is not None and cached[0] is demand:
            return cached[1]
        grouped: Dict[str, List[Tuple[str, float]]] = {}
        for (commodity, tag), need in self.demand_by_tag().items():
            grouped.setdefault(commodity, []).append((tag, need))
        self.readings.by_commodity = (demand, grouped)
        return grouped
