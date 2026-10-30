"""A node can require that a built work be running, not merely known.

`requires_running` on a node lists the ids of works (ventures) that must be built and open. It gates beginning the node,
switches the node's effects off while a work is shut (`running`), and closes the node when it is open as the work closes.
`requires_ways` ({way: kilometres}) asks for a length of road or railway the actor has built. Nothing here names a node."""
from typing import Any, Callable, Collection, Dict, List, Mapping, Optional, Sequence


def unmet_running_gates(needed: Optional[Sequence[str]], done: Collection[str], is_running: Callable[[str], bool]) -> List[str]:
	"""The works a node requires running that are not, in the order the node lists them."""
	if not needed:
		return []
	return [work for work in needed if work not in done or not is_running(work)]


def ways_short(asked: Optional[Mapping[str, float]], built_km_of: Callable[[str], float]) -> Dict[str, float]:
	"""{way: kilometres still to build} of what `requires_ways` asks beyond what is built."""
	if not asked:
		return {}
	short = {way: km - built_km_of(way) for way, km in sorted(asked.items())}
	return {way: gap for way, gap in short.items() if gap > 0.0}


def gate_text(unmet: Sequence[str], short: Optional[Mapping[str, float]], is_visible: Callable[[str], bool],
              is_held: Callable[[str], bool]) -> str:
	"""What to tell a player whose start or opening waits on works that are not running."""
	parts = []
	for work in unmet:
		if not is_visible(work):
			parts.append("a work you have not heard of")
		elif is_held(work):
			parts.append("%s is built but shut ('open %s' or 'restore %s')" % (work, work, work))
		else:
			parts.append("%s is not built yet" % work)
	parts += ["%.3g km more %s must be built" % (gap, way) for way, gap in sorted((short or {}).items())]
	return "it needs a work that is running: " + "; ".join(parts)


def dependents_index(nodes: Mapping[str, Any]) -> Dict[str, List[str]]:
	"""{work id: sorted ids that require it running}, over the whole tree."""
	dependents: Dict[str, List[str]] = {}
	for node_id in sorted(nodes):
		for work in nodes[node_id].get("requires_running") or ():
			dependents.setdefault(work, []).append(node_id)
	return dependents


def lapsed_dependents(dependents: Mapping[str, Sequence[str]], operating: Collection[str],
                      is_unmet: Callable[[str], Any]) -> List[str]:
	"""The open nodes whose required work is no longer running, sorted."""
	return sorted(node_id for works in dependents.values() for node_id in works
	              if node_id in operating and is_unmet(node_id))
