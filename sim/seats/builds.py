"""What the seats have built, taken together: the society sees the work of every seat, not of the acting one.

Pure functions over what each seat holds (`techniques`: seat id to the knowledge module's `SeatTechniques`) and over the
seats mapping. A seat builds a node when it holds it and was not granted it (what its country already had)."""
from typing import Any, Callable, Iterable, List, Mapping, Optional, Set


def builders_of(techniques: Mapping[str, Any], node_id: str) -> List[str]:
	"""Ids of the seats that built `node_id` themselves, in joining order."""
	return [seat_id for seat_id, seat in techniques.items() if node_id in seat.held and node_id not in seat.granted]


def holders_of(techniques: Mapping[str, Any], node_id: str) -> List[str]:
	"""Ids of the seats that hold `node_id` at all, built or granted."""
	return [seat_id for seat_id, seat in techniques.items() if node_id in seat.held]


def built_by_any(techniques: Mapping[str, Any], among: Optional[Iterable[str]] = None) -> Set[str]:
	"""Every node some seat built, limited to `among` when given."""
	wanted = None if among is None else set(among)
	built: Set[str] = set()
	for seat in techniques.values():
		built |= (seat.held - seat.granted) if wanted is None else {
			node_id for node_id in wanted if node_id in seat.held and node_id not in seat.granted}
	return built


def operating_anywhere(seats: Mapping[str, Any], node_id: str) -> bool:
	"""Whether some seat runs `node_id` as a concern: it is then in public use."""
	return any(node_id in seat.projects.operating for seat in seats.values())


def disclosure_modes(techniques: Mapping[str, Any], node_id: str,
                     disclosures_of: Callable[[str], Mapping[str, Any]]) -> List[str]:
	"""What each builder of `node_id` chose to do with it; `disclosures_of` gives a seat's disclosures by node id."""
	return [(disclosures_of(seat_id).get(node_id) or {}).get("mode", "default") for seat_id in builders_of(techniques, node_id)]


def licensors_of(techniques: Mapping[str, Any], node_id: str, licensee_id: str,
                 disclosures_of: Callable[[str], Mapping[str, Any]]) -> List[str]:
	"""The seats that licensed `node_id` to `licensee_id`."""
	return [seat_id for seat_id in builders_of(techniques, node_id)
	        if licensee_id in ((disclosures_of(seat_id).get(node_id) or {}).get("licensees") or {})]
