"""The root's registry of seats: one household facade per seat, and `act_as` to rebind the root aliases to a seat. Plain functions
of the `Sim`; its methods of the same names call these."""
import contextlib

from sim.agents.api import Household, HouseholdParty
from sim.knowledge.api import ReceiveTechniques
from .agents_port_household import HouseholdPort
from . import game_assembly
from .state_seat import SeatState, bind_seat


def add_seat(sim, seat_id: str, seat: SeatState) -> None:
	"""Register a seat and give it its own household facade."""
	if seat_id in sim.state.seats:
		raise ValueError("seat %r already exists" % (seat_id,))
	sim.state.seats[seat_id] = seat
	if getattr(sim, "assembly", None) is not None:   # a test host built without a game has none
		game_assembly.give_seat_slots(sim.assembly, seat)
	sim.state.attach_purses()
	sim._seat_facades[seat_id] = sim._new_facade(seat_id)


def new_facade(sim, seat_id: str) -> Household:
	"""A household facade for `seat_id`, hooked to that seat's own containers."""
	acting = sim.state.acting_seat
	bind_seat(sim.state, seat_id)
	try:
		held = sim.state.household
		cash_mark = held.cash_mark
		facade = Household(
			starting_capital=held.capital,
			operating_changed=sim._operating_changed,
			active_changed=sim._active_changed,
			state=sim.state,
			port=HouseholdPort(),
			techniques_held=lambda: sim.view("techniques_held")())
		held.cash_mark = cash_mark
	finally:
		bind_seat(sim.state, acting)
	return facade


def seat_party(sim, seat_id: str, margins=None) -> HouseholdParty:
	"""`seat_id` as an actor an exchange can deal with: it holds patents and shares, pays and is paid."""
	return HouseholdParty(sim._seat_facades[seat_id], margins, seat_id, sim.act_as,
	                      dealings=sim.state.seats[seat_id].modules["seats"],
	                      receive=lambda nodes, granted: sim.send(ReceiveTechniques(tuple(nodes), granted)))


def seat_parties(sim) -> dict:
	"""Every seat as an actor, by seat id."""
	return {seat_id: sim.seat_party(seat_id) for seat_id in sim.state.seats}


def switch_seat(sim, seat_id: str) -> None:
	bind_seat(sim.state, seat_id)
	sim.household = sim._seat_facades[seat_id]
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


def sync_seat_facades(sim) -> None:
	"""After a load: each saved seat has a facade on the loaded state and the acting seat's is `sim.household`."""
	facades = sim._seat_facades
	for seat_id in list(facades):
		if seat_id not in sim.state.seats:
			del facades[seat_id]
	for seat_id in sim.state.seats:
		if seat_id in facades:
			facades[seat_id]._state = sim.state
		else:
			facades[seat_id] = sim._new_facade(seat_id)
	sim.household = facades[sim.state.acting_seat]
