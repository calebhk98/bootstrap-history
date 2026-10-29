"""How the order the household's hours serve projects changes: plain functions of the order and the projects in hand."""
from typing import Iterable, List, Sequence


def put_first(order: Sequence[str], node_id: str) -> List[str]:
	"""The order with `node_id` at the front (moved there if it was already in it)."""
	return [node_id] + [other for other in order if other != node_id]


def place_sequence(order: Sequence[str], active: Iterable[str], sequence: Sequence[str]) -> List[str]:
	"""The order with the places the active projects hold (and new places at the end for nodes the order lacks) refilled
	from `sequence`, first place first."""
	active = set(active)
	present = set(order)
	missing = [node_id for node_id in sequence if node_id not in present]
	placed = list(order) + missing
	slots = [place for place, node_id in enumerate(order) if node_id in active]
	slots += list(range(len(order), len(placed)))
	for slot, node_id in zip(sorted(slots), sequence):
		placed[slot] = node_id
	return placed
