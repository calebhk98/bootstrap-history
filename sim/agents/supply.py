"""What an actor's concerns put on the market, in the tree's own terms.

A concern makes the materials whose production entries it gates (`requires_node`) or operates (`operated_by`).
One that declares a physical yearly output (`annual_output_t`) puts that on the market; one that declares none
puts on what its staff and plant turn out, which the engine derives from the production data and hands in. The
market reads the total through the markets module's actor_supply view.
"""
from typing import Any, Dict, FrozenSet, List

# {id of a production table: (the table, nodes by material, materials by node)}; the table is kept so a hit is confirmed with `is`
_INDEXES: Dict[int, Any] = {}


def _indexes(production: Any = None) -> Any:
	if production is None:
		from sim.world.demand import production_data
		production = production_data()
	held = _INDEXES.get(id(production))
	if held is None or held[0] is not production:
		made_by = {}
		for entry in production.values():
			for gate in dict.fromkeys([entry.get("requires_node"), *(entry.get("operated_by") or [])]):
				if gate:
					made_by.setdefault(gate, set()).update((entry.get("outputs") or {}))
		by_node = {gate: sorted(materials) for gate, materials in made_by.items()}
		by_material: Dict[str, Any] = {}
		for gate, materials in made_by.items():
			for material in materials:
				by_material.setdefault(material, set()).add(gate)
		held = _INDEXES[id(production)] = (production, {material: frozenset(gates) for material, gates in by_material.items()}, by_node)
	return held[1], held[2]


def materials_made_by(node_id: str, production: Any = None) -> List[str]:
	"""Materials whose production entries (of `production`, else the repository's) become available with this node, in id order."""
	return _indexes(production)[1].get(node_id, [])


def nodes_making(material: str, production: Any = None) -> FrozenSet[str]:
	"""Nodes whose production entries make `material`."""
	return _indexes(production)[0].get(material, frozenset())


def concern_output_tonnes(node: Any, node_id: str, material: str, ramp: float, staffed: float,
						  derived_tonnes: float = 0.0, production: Any = None) -> float:
	"""Tonnes a year of `material` one concern puts on the market, scaled by ramp-up and the share of its staff
	found: its declared output split evenly across the materials it makes, else `derived_tonnes`, what its
	staff and plant turn out of the material by the production data."""
	declared = float(node.get("annual_output_t") or 0.0)
	if declared <= 0.0:
		return max(0.0, derived_tonnes) * ramp * staffed
	made = materials_made_by(node_id, production)
	if material not in made:
		return 0.0
	return declared * ramp * staffed / len(made)
