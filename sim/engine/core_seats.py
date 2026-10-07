"""Switching the acting seat: which player's household, projects and founder the root state shows."""
import contextlib

from sim.agents.api import Household
from .agents_port_household import HouseholdPort
from .state_seat import SeatState, bind_seat


class SeatMixin:
	"""One household facade per seat, and `act_as` to rebind the root aliases to a seat."""

	def add_seat(self, seat_id: str, seat: SeatState) -> None:
		"""Register a seat and give it its own household facade."""
		if seat_id in self.state.seats:
			raise ValueError("seat %r already exists" % (seat_id,))
		self.state.seats[seat_id] = seat
		self._seat_facades[seat_id] = self._new_facade(seat_id)

	def _new_facade(self, seat_id: str) -> Household:
		"""A household facade for `seat_id`, hooked to that seat's own containers."""
		acting = self.state.acting_seat
		bind_seat(self.state, seat_id)
		try:
			held = self.state.household
			cash_mark = held.cash_mark
			facade = Household(
				starting_capital=held.capital,
				operating_changed=self._operating_changed,
				active_changed=self._active_changed,
				workforce_changed=self._workforce_changed,
				state=self.state,
				port=HouseholdPort())
			held.cash_mark = cash_mark
		finally:
			bind_seat(self.state, acting)
		return facade

	def _switch_seat(self, seat_id: str) -> None:
		bind_seat(self.state, seat_id)
		self.household = self._seat_facades[seat_id]
		self._reset_economic_caches()

	@contextlib.contextmanager
	def act_as(self, seat_id: str):
		"""Run the body as `seat_id`, then restore the seat that was acting."""
		if seat_id not in self.state.seats:
			raise KeyError("no seat %r" % (seat_id,))
		previous = self.state.acting_seat
		if seat_id != previous:
			self._switch_seat(seat_id)
		try:
			yield self
		finally:
			if self.state.acting_seat != previous:
				self._switch_seat(previous)

	def sync_seat_facades(self) -> None:
		"""After a load: each saved seat has a facade on the loaded state and the acting seat's is `self.household`."""
		facades = self._seat_facades
		for seat_id in list(facades):
			if seat_id not in self.state.seats:
				del facades[seat_id]
		for seat_id in self.state.seats:
			if seat_id in facades:
				facades[seat_id]._state = self.state
			else:
				facades[seat_id] = self._new_facade(seat_id)
		self.household = facades[self.state.acting_seat]
