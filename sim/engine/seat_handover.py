"""Handing a seat over: its known nodes, holdings and goal pass to a named replacement seat and the old seat leaves.

The replacement keeps its own founder (the leaver's run is over). Everything else a seat owns moves as the same
objects: household, projects (the known nodes), holdings, institutions, goal record, chosen goal and country.
Records keyed to the country (the relations store) therefore stay with the country the replacement now plays for.
A country seat uses the same path: its country is just one more field of the seat."""
from typing import Mapping, Optional

from sim.refusal import Refusal

MOVED_FIELDS = ("household", "projects", "holdings", "governance", "seat_progress", "goal", "country")


def handover_refusal(seats: Mapping, from_id: str, to_id: str) -> Optional[Refusal]:
	"""Why `from_id` cannot hand over to `to_id`, or None when it can."""
	known = list(seats)
	for role, seat_id in (("from", from_id), ("to", to_id)):
		if seat_id not in seats:
			return Refusal("unknown_seat", "there is no seat %r to hand %s. The seats are: %s. Nothing was changed."
			               % (seat_id, role, ", ".join(known)), choices=known, seat=seat_id)
	if from_id == to_id:
		return Refusal("same_seat", "a seat cannot be handed to itself. Nothing was changed.", seat=from_id)
	return None


def move_seat_fields(seats: dict, from_id: str, to_id: str) -> dict:
	"""Give the replacement the leaver's seat fields and drop the leaver from `seats`. Returns what moved."""
	source, target = seats[from_id], seats[to_id]
	for name in MOVED_FIELDS:
		setattr(target, name, getattr(source, name))
	del seats[from_id]
	return {"from": from_id, "to": to_id, "known_nodes": len(target.projects.done), "country": target.country}


class SeatHandoverMixin:

	def hand_over_seat(self, from_id: str, to_id: str):
		"""Pass `from_id`'s seat to `to_id`: fields (above), the cash in its purse, and it leaves the year.
		Returns a Refusal that changed nothing, or the dict `move_seat_fields` answers."""
		refusal = handover_refusal(self.state.seats, from_id, to_id)
		if refusal:
			return refusal
		purses = self.state.actors.purses if self.state.actors is not None else None
		cash = purses.net(from_id) if purses is not None and purses.has_account(from_id) else 0.0
		moved = move_seat_fields(self.state.seats, from_id, to_id)
		self._seat_facades.pop(from_id, None)
		self.state.attach_purses()
		if purses is not None and cash > 0.0:
			purses.transfer(from_id, to_id, cash, "handover")
		if self.state.acting_seat == from_id:
			self._switch_seat(to_id)
		if getattr(self, "session_seat", None) == from_id:
			self.session_seat = to_id
		self._reset_economic_caches()
		return moved
