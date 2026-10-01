"""What an actor's concerns put on the market, in the tree's own terms.

A concern that declares a physical yearly output (`annual_output_t`) makes the
materials whose production entries it gates (`requires_node`). The market reads
the total through `Sim.actor_supply(material)`.
"""
from typing import Any, Dict, List

_MATERIALS_BY_NODE: Dict[int, Dict[str, List[str]]] = {}


def materials_made_by(node_id: str) -> List[str]:
	"""Materials whose production entries become available with this node, in id order."""
	from sim.world.labour_market import production_data
	production = production_data()
	index = _MATERIALS_BY_NODE.get(id(production))
	if index is None:
		index = {}
		for entry in production.values():
			gate = entry.get("requires_node")
			if gate:
				index.setdefault(gate, set()).update((entry.get("outputs") or {}))
		index = {gate: sorted(materials) for gate, materials in index.items()}
		_MATERIALS_BY_NODE.clear()
		_MATERIALS_BY_NODE[id(production)] = index
	return index.get(node_id, [])


def concern_output_tonnes(node: Any, node_id: str, material: str, ramp: float, staffed: float) -> float:
	"""Tonnes a year of `material` one concern puts on the market: its declared output,
	split evenly across the materials it makes, scaled by ramp-up and the share of its staff found."""
	declared = float(node.get("annual_output_t") or 0.0)
	made = materials_made_by(node_id)
	if declared <= 0.0 or material not in made:
		return 0.0
	return declared * ramp * staffed / len(made)
