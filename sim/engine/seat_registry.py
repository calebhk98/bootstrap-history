"""The root's registry of seats: adding one, and `act_as` (the assembly's switch) as the game's context manager. Plain functions
of the `Sim`; its methods of the same names call these."""
import contextlib
from typing import Any, Mapping, Optional

from sim.projects.api import WatchActive
from sim.refusal import Refusal
from sim.ventures.api import WatchBusiness
from . import game_assembly
from .seat_defaults import default_policy
from .state_seat import SeatState, seat_from_template


def add_seat(sim, seat_id: str, seat: SeatState) -> None:
	"""Register a seat."""
	if seat_id in sim.state.seats:
		raise ValueError("seat %r already exists" % (seat_id,))
	sim.state.seats[seat_id] = seat
	if getattr(sim, "assembly", None) is not None:   # a test host built without a game has none
		game_assembly.give_seat_slots(sim.assembly, seat)
		sim.send(WatchActive(seat_id))
		sim.send(WatchBusiness(seat_id))


def register_seat(sim, seat_id: str, template: Mapping[str, Any]) -> Optional[Refusal]:
	"""Register a seat built from `template` with the standing policy a new seat starts with; a Refusal when the id is taken."""
	if seat_id in sim.state.seats:
		return Refusal("seat_exists", "seat %r already exists" % (seat_id,), seat=seat_id)
	add_seat(sim, seat_id, seat_from_template(template, default_policy(sim.manual)))
	return None


@contextlib.contextmanager
def act_as(sim, seat_id: str):
	"""Run the body as `seat_id`, then restore the seat that was acting."""
	with sim.assembly.act_as(seat_id):
		yield sim
