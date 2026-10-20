"""Handing a seat over: its known nodes, holdings and goal pass to a named replacement seat and the old seat leaves.

The replacement keeps its own founder (the leaver's run is over). Everything else a seat owns moves as the same
objects: household, projects (the known nodes), holdings, institutions, goal record, chosen goal and country.
Records keyed to the country (the relations store) therefore stay with the country the replacement now plays for.
A country seat uses the same path: its country is just one more field of the seat.

The replacement is a seat already in the game and must hold no works, staff, holdings or institutions of its own
(`holds_that_would_be_lost`): those would be overwritten, so a replacement that holds some is refused. What merges
without loss is added: its cash, deposits and debts join the leaver's under the replacement's id, and the techniques
it knows join the leaver's. Everything keyed by the leaver's id outside the seat is renamed to the replacement's
(seat_handover_rekey.py), the leaver's debts and claims with it, so a handover pays and forgives nothing."""
from typing import Mapping, Optional

from sim.refusal import Refusal

from .seat_handover_empty import holds_that_would_be_lost
from .seat_handover_rekey import rename_seat_references

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
	holds = holds_that_would_be_lost(seats[to_id])
	if holds:
		return Refusal("replacement_not_empty", "seat %r already has %s, which a handover would overwrite. Hand over to an empty "
		               "seat (join adds one). Nothing was changed." % (to_id, ", ".join(holds)), seat=to_id, holds=holds)
	return None


def move_seat_fields(seats: dict, from_id: str, to_id: str) -> dict:
	"""Give the replacement the leaver's seat fields and drop the leaver from `seats`. Returns what moved."""
	source, target = seats[from_id], seats[to_id]
	source.projects.done |= target.projects.done
	source.projects.granted |= target.projects.granted
	for name in MOVED_FIELDS:
		setattr(target, name, getattr(source, name))
	del seats[from_id]
	return {"from": from_id, "to": to_id, "known_nodes": len(target.projects.done), "country": target.country}


class SeatHandoverMixin:

	def hand_over_seat(self, from_id: str, to_id: str):
		"""Pass `from_id`'s seat to `to_id`: fields (above), its account with the debts and claims, and whatever else is
		keyed by its id; it leaves the year. Returns a Refusal that changed nothing, or the dict `move_seat_fields` answers."""
		refusal = handover_refusal(self.state.seats, from_id, to_id)
		if refusal:
			return refusal
		moved = move_seat_fields(self.state.seats, from_id, to_id)
		self._seat_facades.pop(from_id, None)
		rename_seat_references(self, from_id, to_id)
		self.state.attach_purses()
		if self.state.acting_seat == from_id:
			self._switch_seat(to_id)
		if getattr(self, "session_seat", None) == from_id:
			self.session_seat = to_id
		self._reset_economic_caches()
		return moved
