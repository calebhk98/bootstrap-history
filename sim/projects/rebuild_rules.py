"""What a forgotten technology still has going for it when it is rebuilt, as functions of the facts that decide it.

A node lost to a sack is not the same as a node never built: a dispersed copy of the record, people who still practise
its trades, and plant built on it all survive. Each is a share between zero and one; together they set the share of the
original work a rebuild does not have to redo."""
from typing import Any, Collection, Dict, List, Mapping, Sequence


def dependents_index(nodes: Mapping[str, Any]) -> Dict[str, List[str]]:
	"""{node id: ids of nodes listing it as a prerequisite}, in the tree's order."""
	index: Dict[str, List[str]] = {}
	for node_id, node in nodes.items():
		for prerequisite in node["pre"]:
			index.setdefault(prerequisite, []).append(node_id)
	return index


def copy_share(none_chance: float, chance: float) -> float:
	"""How much of the loss a dispersed copy of the record spares: the loss chance now against the chance with no hedge."""
	return max(0.0, (none_chance - chance) / none_chance) if none_chance > 0 else 0.0


def practice_share(trades: Sequence[str], employees: Mapping[str, float]) -> float:
	"""The share of the node's trades still worked by at least one person kept on the books."""
	if not trades:
		return 0.0
	return sum(1 for trade in trades if employees.get(trade, 0.0) >= 1.0) / len(trades)


def plant_share(dependents: Sequence[str], done: Collection[str]) -> float:
	"""The share of what was built on the node that still stands."""
	if not dependents:
		return 0.0
	return sum(1 for dependent in dependents if dependent in done) / len(dependents)


def retained_share(survivals: Mapping[str, float], ceiling: float) -> float:
	"""The share of the original work a rebuild skips, never more than `ceiling`."""
	missing = 1.0
	for share in survivals.values():
		missing *= 1.0 - share
	return ceiling * (1.0 - missing)


SURVIVAL_WORDS = {"copy": "a copy of the record survives",
                  "practice": "people who practise its trades are still on your books",
                  "plant": "plant built on it still stands"}


def explanation(forgotten_year: int, survivals: Mapping[str, float], retained: float) -> str:
	"""One line for `why` on a lost node: what a rebuild keeps and why."""
	kept = [SURVIVAL_WORDS[kind] for kind, share in survivals.items() if share > 0]
	return ("forgotten in %d. A rebuild redoes %d%% of the original work, money and "
	        "calendar (%d%% is saved) because %s."
	        % (forgotten_year,
	           round((1.0 - retained) * 100), round(retained * 100),
	           " and ".join(kept) if kept else
	           "nothing of it survives: no copy, no practitioners, no plant, "
	           "so it costs what a first build does"))
