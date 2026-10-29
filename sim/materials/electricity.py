"""Electricity as a physical quantity: what the seat can generate and what its work in hand draws."""
from typing import Any, Dict, Set, Tuple

from . import rules


class Electricity:
    """Needs: mechanic, tree_nodes, legacy_projects, operating, hard_prerequisites."""

    def anchor_kw(self, tier: str) -> float:
        return self.needs.mechanic["power_tier"][tier]["anchor_kw"]

    def generation_breakdown_kw(self) -> Dict[str, Any]:
        """What the seat can generate and transmit in kilowatts: local, grid and transmission capacity, the best mechanical
        prime mover of each family (informational) and the sources the built nodes declare. `total_kw` is what the throttle
        checks electrical demand against."""
        mechanic = self.needs.mechanic
        return rules.generation_breakdown(self.needs.techniques_held(), self.needs.tree_nodes(),
                                          mechanic["power_generation"], mechanic["prime_mover"], self.anchor_kw)

    def installed_generation_kw_by_tier(self) -> Dict[str, float]:
        return rules.installed_by_tier(self.needs.techniques_held(), self.needs.mechanic["power_generation"],
                                       self.anchor_kw)

    def generation_capacity_kw(self) -> float:
        return self.generation_breakdown_kw()["total_kw"]

    def electrical_processes(self) -> Dict[str, Tuple[str, float]]:
        """{node id: (material key, kWh per kg of that material)} from the `electrical_process` mechanic."""
        return {node_id: (spec["material"], spec["kwh_per_kg_of_product"] / spec["kg_material_per_kg_product"])
                for node_id, spec in self.needs.mechanic["electrical_process"].items()}

    def electricity_load_node_ids(self) -> Set[str]:
        """Every node whose own prerequisite closure needs generated electricity and that draws material: worked out once
        from the static tree, in one memoised walk."""
        if self._load_ids is not None:
            return self._load_ids
        tokens = frozenset(self.needs.mechanic["electricity_gate"])
        nodes = self.needs.tree_nodes()
        hard_prerequisites = self.needs.hard_prerequisites
        memo: Dict[str, bool] = {}

        def gated(node_id: str, on_stack: Set[str]) -> bool:
            if node_id in memo:
                return memo[node_id]
            if node_id in tokens:
                memo[node_id] = True
                return True
            if node_id in on_stack or node_id not in nodes:
                return False       # a cycle answers "not gated" rather than recursing for ever
            on_stack.add(node_id)
            result = any(gated(parent_id, on_stack) for parent_id in hard_prerequisites[node_id])
            on_stack.discard(node_id)
            memo[node_id] = result
            return result

        # a thing under construction draws power because the work is happening, not because it pays rent
        self._load_ids = {node_id for node_id, node in nodes.items() if node.get("mat") and gated(node_id, set())}
        return self._load_ids

    def node_annual_tonnes(self, node_id: str, material: str) -> float:
        """Tonnes a year ONE node draws of `material`, as the annual demand counts it."""
        projects = self.needs.legacy_projects()
        return rules.node_annual_tonnes(self.needs.tree_nodes().get(node_id), material, node_id in projects.active,
                                        node_id in self.needs.techniques_held())

    def electricity_demand_kw(self) -> float:
        """Average continuous kW drawn by work in hand."""
        projects = self.needs.legacy_projects()
        return rules.electricity_demand_kw(self.electrical_processes(), self.node_annual_tonnes,
                                           self.electricity_load_node_ids(), self.needs.tree_nodes(), projects.active,
                                           self.needs.techniques_held(), self.needs.operating())
