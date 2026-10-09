"""What the seats have built, taken together: the society sees the work of every seat, not of the acting one.

Pure functions over the seats mapping, then the Sim methods that use them. A seat builds a node when it is in
the seat's `done` and not in its `granted` (what its country already had)."""
from typing import Iterable, List, Mapping, Optional, Set

from .state_seat import SeatState


def builders_of(seats: Mapping[str, SeatState], node_id: str) -> List[str]:
	"""Ids of the seats that built `node_id` themselves, in joining order."""
	return [seat_id for seat_id, seat in seats.items()
	        if node_id in seat.projects.done and node_id not in seat.projects.granted]


def holders_of(seats: Mapping[str, SeatState], node_id: str) -> List[str]:
	"""Ids of the seats that hold `node_id` at all, built or granted."""
	return [seat_id for seat_id, seat in seats.items() if node_id in seat.projects.done]


def built_by_any(seats: Mapping[str, SeatState], among: Optional[Iterable[str]] = None) -> Set[str]:
	"""Every node some seat built, limited to `among` when given."""
	wanted = None if among is None else set(among)
	built: Set[str] = set()
	for seat in seats.values():
		built |= (seat.projects.done - seat.projects.granted) if wanted is None else {
			node_id for node_id in wanted if node_id in seat.projects.done and node_id not in seat.projects.granted}
	return built


def earliest_done_year(seats: Mapping[str, SeatState], node_id: str, default: int) -> int:
	"""The year the first seat to hold `node_id` finished it (`default` for a seat with no record)."""
	years = [(seat.projects.done_year or {}).get(node_id, default) for seat in seats.values()
	         if node_id in seat.projects.done]
	return min(years) if years else default


def operating_anywhere(seats: Mapping[str, SeatState], node_id: str) -> bool:
	"""Whether some seat runs `node_id` as a concern: it is then in public use."""
	return any(node_id in seat.projects.operating for seat in seats.values())


def disclosure_modes(seats: Mapping[str, SeatState], node_id: str) -> List[str]:
	"""What each builder of `node_id` chose to do with it."""
	return [(seats[seat_id].projects.disclosures.get(node_id) or {}).get("mode", "default")
	        for seat_id in builders_of(seats, node_id)]


def licensors_of(seats: Mapping[str, SeatState], node_id: str, licensee_id: str) -> List[str]:
	"""The seats that licensed `node_id` to `licensee_id`."""
	return [seat_id for seat_id in builders_of(seats, node_id)
	        if licensee_id in ((seats[seat_id].projects.disclosures.get(node_id) or {}).get("licensees") or {})]


class SeatBuildsMixin:

	def seats_that_built(self, node_id: str) -> List[str]:
		return builders_of(self.state.seats, node_id)

	def seat_place(self, seat_id: str) -> str:
		"""Where a seat works from: its base tile."""
		with self.act_as(seat_id):
			return str(self.labour.base_tile())
