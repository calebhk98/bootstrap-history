"""What the seats have built, taken together: the society sees the work of every seat, not of the acting one.

Pure functions over the seats mapping. A seat builds a node when it is in
the seat's `done` and not in its `granted` (what its country already had)."""
from typing import Any, Callable, Iterable, List, Mapping, Optional, Set


def builders_of(seats: Mapping[str, Any], node_id: str) -> List[str]:
	"""Ids of the seats that built `node_id` themselves, in joining order."""
	return [seat_id for seat_id, seat in seats.items()
	        if node_id in seat.projects.done and node_id not in seat.projects.granted]


def holders_of(seats: Mapping[str, Any], node_id: str) -> List[str]:
	"""Ids of the seats that hold `node_id` at all, built or granted."""
	return [seat_id for seat_id, seat in seats.items() if node_id in seat.projects.done]


def built_by_any(seats: Mapping[str, Any], among: Optional[Iterable[str]] = None) -> Set[str]:
	"""Every node some seat built, limited to `among` when given."""
	wanted = None if among is None else set(among)
	built: Set[str] = set()
	for seat in seats.values():
		built |= (seat.projects.done - seat.projects.granted) if wanted is None else {
			node_id for node_id in wanted if node_id in seat.projects.done and node_id not in seat.projects.granted}
	return built


def operating_anywhere(seats: Mapping[str, Any], node_id: str) -> bool:
	"""Whether some seat runs `node_id` as a concern: it is then in public use."""
	return any(node_id in seat.projects.operating for seat in seats.values())


def disclosure_modes(seats: Mapping[str, Any], node_id: str,
                     disclosures_of: Callable[[str], Mapping[str, Any]]) -> List[str]:
	"""What each builder of `node_id` chose to do with it; `disclosures_of` gives a seat's disclosures by node id."""
	return [(disclosures_of(seat_id).get(node_id) or {}).get("mode", "default") for seat_id in builders_of(seats, node_id)]


def licensors_of(seats: Mapping[str, Any], node_id: str, licensee_id: str,
                 disclosures_of: Callable[[str], Mapping[str, Any]]) -> List[str]:
	"""The seats that licensed `node_id` to `licensee_id`."""
	return [seat_id for seat_id in builders_of(seats, node_id)
	        if licensee_id in ((disclosures_of(seat_id).get(node_id) or {}).get("licensees") or {})]
