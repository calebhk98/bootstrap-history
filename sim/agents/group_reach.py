"""Which commodities and goods categories a technique touches, for a prohibition on techniques that hurt a group."""
from typing import Any, Callable, Dict, List, Set

from .group_tuning import REACH_REFINEMENT_DEPTH


def subjects_reached(node_id: str, nodes: Dict[str, Dict[str, Any]], made_by: Callable[[str], List[str]],
					 commodity_of: Callable[[str], str]) -> Set[str]:
	"""The commodities the node makes, its own category, and the commodities made by the techniques
	of its own category that it refines (its prerequisites, a few steps back): the line it belongs to."""
	node = nodes.get(node_id) or {}
	category = node.get("cat")
	reached = {commodity_of(material) for material in made_by(node_id)}
	if category:
		reached.add(category)
	frontier = [node_id]
	seen = {node_id}
	for _step in range(REACH_REFINEMENT_DEPTH):
		frontier = [prerequisite for current in frontier for prerequisite in (nodes.get(current) or {}).get("pre") or ()
					if prerequisite not in seen and (nodes.get(prerequisite) or {}).get("cat") == category]
		seen.update(frontier)
		for ancestor in frontier:
			reached.update(commodity_of(material) for material in made_by(ancestor))
	return reached
