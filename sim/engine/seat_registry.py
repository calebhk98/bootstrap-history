"""The root's registry of seats: adding one, and `act_as` (the assembly's switch) as the game's context manager. Plain functions
of the `Sim`; its methods of the same names call these."""
import contextlib

from sim.projects.api import WatchActive
from sim.ventures.api import WatchBusiness
from . import game_assembly
from .state_seat import SeatState


def add_seat(sim, seat_id: str, seat: SeatState) -> None:
	"""Register a seat."""
	if seat_id in sim.state.seats:
		raise ValueError("seat %r already exists" % (seat_id,))
	sim.state.seats[seat_id] = seat
	if getattr(sim, "assembly", None) is not None:   # a test host built without a game has none
		game_assembly.give_seat_slots(sim.assembly, seat)
		sim.send(WatchActive(seat_id))
		sim.send(WatchBusiness(seat_id))


@contextlib.contextmanager
def act_as(sim, seat_id: str):
	"""Run the body as `seat_id`, then restore the seat that was acting."""
	with sim.assembly.act_as(seat_id):
		yield sim
