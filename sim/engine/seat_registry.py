"""The root's registry of seats, and `act_as` to rebind the root aliases to a seat. Plain functions of the `Sim`; its methods of the
same names call these."""
import contextlib

from sim.projects.api import WatchActive
from sim.ventures.api import WatchBusiness
from . import game_assembly
from .state_seat import SeatState, bind_seat


def add_seat(sim, seat_id: str, seat: SeatState) -> None:
	"""Register a seat."""
	if seat_id in sim.state.seats:
		raise ValueError("seat %r already exists" % (seat_id,))
	sim.state.seats[seat_id] = seat
	if getattr(sim, "assembly", None) is not None:   # a test host built without a game has none
		game_assembly.give_seat_slots(sim.assembly, seat)
		sim.send(WatchActive(seat_id))
		sim.send(WatchBusiness(seat_id))


def switch_seat(sim, seat_id: str) -> None:
	bind_seat(sim.state, seat_id)
	game_assembly.switch_seat(sim, seat_id)     # the modules answer for the new seat before its caches are forgotten
	sim._reset_economic_caches()


@contextlib.contextmanager
def act_as(sim, seat_id: str):
	"""Run the body as `seat_id`, then restore the seat that was acting."""
	if seat_id not in sim.state.seats:
		raise KeyError("no seat %r" % (seat_id,))
	previous = sim.state.acting_seat
	if seat_id != previous:
		sim._switch_seat(seat_id)
	try:
		yield sim
	finally:
		if sim.state.acting_seat != previous and previous in sim.state.seats:   # a handover removes a seat
			sim._switch_seat(previous)
