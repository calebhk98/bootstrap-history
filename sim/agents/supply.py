"""What an actor's concerns put on the market, in the tree's own terms.

A concern that declares a physical yearly output (`annual_output_t`) makes the
materials whose production entries it gates (`requires_node`). The market reads
the total through `Sim.actor_supply(material)`.
"""
from typing import Any, Dict, FrozenSet, List

# (production table, nodes by material, materials by node): the table is kept so a hit is confirmed with `is`
_INDEXES: List[Any] = [None, None, None]


def _indexes() -> Any:
	from sim.labour.api import production_data
	production = production_data()
	if _INDEXES[0] is not production:
		made_by = {}
		for entry in production.values():
			gate = entry.get("requires_node")
			if gate:
				made_by.setdefault(gate, set()).update((entry.get("outputs") or {}))
		by_node = {gate: sorted(materials) for gate, materials in made_by.items()}
		by_material: Dict[str, Any] = {}
		for gate, materials in made_by.items():
			for material in materials:
				by_material.setdefault(material, set()).add(gate)
		_INDEXES[:] = [production, {material: frozenset(gates) for material, gates in by_material.items()}, by_node]
	return _INDEXES[1], _INDEXES[2]


def materials_made_by(node_id: str) -> List[str]:
	"""Materials whose production entries become available with this node, in id order."""
	return _indexes()[1].get(node_id, [])


def nodes_making(material: str) -> FrozenSet[str]:
	"""Nodes whose production entries make `material`."""
	return _indexes()[0].get(material, frozenset())


def concern_output_tonnes(node: Any, node_id: str, material: str, ramp: float, staffed: float) -> float:
	"""Tonnes a year of `material` one concern puts on the market: its declared output,
	split evenly across the materials it makes, scaled by ramp-up and the share of its staff found."""
	declared = float(node.get("annual_output_t") or 0.0)
	made = materials_made_by(node_id)
	if declared <= 0.0 or material not in made:
		return 0.0
	return declared * ramp * staffed / len(made)
