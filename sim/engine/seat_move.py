"""Moving a seat to another id in the seat registry: the leaver's seat fields pass to the replacement and the leaver leaves.

Everything a seat owns moves as the same objects, every module's seat state with it (`modules`, the seats module's goal,
country and kind among them). The replacement keeps its own founder record (the leaver's run is over). What the replacement had of its own was checked empty or mergeable by the seats
module before this runs (sim/seats/handover_rules.py)."""
from sim.knowledge.api import HandOverTechniques
from . import game_assembly
from .seat_handover_rekey import rename_seat_references

MOVED_FIELDS = ("household", "holdings", "seat_progress", "modules")


def move_seat_fields(seats: dict, from_id: str, to_id: str) -> dict:
	"""Give the replacement the leaver's seat fields and drop the leaver from `seats`. Returns what moved."""
	source, target = seats[from_id], seats[to_id]
	for name in MOVED_FIELDS:
		setattr(target, name, getattr(source, name))
	del seats[from_id]
	return {"from": from_id, "to": to_id, "country": target.modules["seats"].country}


def move_seat(sim, from_id: str, to_id: str) -> dict:
	"""Move the seat in the registry, rename it in every store the engine keeps keyed by seat id, and rebind the game to
	the seat that now acts. Returns `move_seat_fields`'s account."""
	known_nodes = sim.send(HandOverTechniques(from_id, to_id))   # the leaver's knowledge record is the one that moves
	moved = move_seat_fields(sim.state.seats, from_id, to_id)
	moved["known_nodes"] = known_nodes
	sim._seat_facades.pop(from_id, None)
	rename_seat_references(sim, from_id, to_id)
	sim.state.attach_purses()
	if sim.state.acting_seat == from_id:
		sim._switch_seat(to_id)
	else:
		game_assembly.switch_seat(sim, sim.state.acting_seat)   # the modules' seat state moved with the seat
	if getattr(sim, "session_seat", None) == from_id:
		sim.session_seat = to_id
	sim._reset_economic_caches()
	return moved
