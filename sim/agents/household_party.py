"""A seat's household as a party to an exchange.

An exchange handles an actor with `actor_id`, `money`, `concerns`, `knows`, `learn`, `credit`, `debit`,
`opened_year_of`, `capacity_of` and a `record` (stores, offers, opened year, margins, patents, shares). The
household keeps that state in the simulation state, so this adapter maps the names onto it: concerns are the
household's operating set, opened years, patents and shares held its seat's own dictionaries, and the purse
its capital. The seat's id is the party's `actor_id`; `act_as` (the engine's seat switch) makes every access
read the seat's own state when another seat is acting.
"""
import contextlib
from typing import Any, Callable, Dict, Optional

from .records import ActorRecord


class SeatRecord(ActorRecord):
	"""An actor record whose patents, shares and issued equity are the seat's own, so they persist and write through."""

	seat_holdings: Any = None

	@property
	def issued(self) -> float:
		return self.seat_holdings.shares_issued if self.seat_holdings is not None else 0.0

	@issued.setter
	def issued(self, value: float) -> None:
		if self.seat_holdings is not None:
			self.seat_holdings.shares_issued = value

	@property
	def offers(self) -> Any:
		return self.seat_holdings.offers if self.seat_holdings is not None else []

	@offers.setter
	def offers(self, value: Any) -> None:
		if self.seat_holdings is not None:
			self.seat_holdings.offers = value

	@property
	def offer_serial(self) -> int:
		return self.seat_holdings.offer_serial if self.seat_holdings is not None else 0

	@offer_serial.setter
	def offer_serial(self, value: int) -> None:
		if self.seat_holdings is not None:
			self.seat_holdings.offer_serial = value


class HouseholdParty:
	"""Gives a `Household` the surface an exchange needs; holds no state of its own beyond a transient record."""

	kind = "household"

	def __init__(self, household: Any, margins: Optional[Dict[str, float]] = None, seat_id: Optional[str] = None,
				act_as: Optional[Callable[[str], Any]] = None) -> None:
		self.household = household
		state = household._state
		self.actor_id = seat_id if seat_id is not None else state.acting_seat
		self._act_as = act_as
		seat = state.seats[self.actor_id]
		if seat.projects.opened_year is None:
			seat.projects.opened_year = {}
		# the seat's own dictionaries, so opening, closing, patenting and trading shares write through
		self.record = SeatRecord(kind="household", opened_year=seat.projects.opened_year, margins=dict(margins or {}),
								patents=seat.holdings.patents, holdings=seat.holdings.shares_held)
		self.record.seat_holdings = seat.holdings

	def _acting(self) -> Any:
		return self._act_as(self.actor_id) if self._act_as is not None else contextlib.nullcontext()

	@property
	def money(self) -> float:
		with self._acting():
			return self.household.money

	@money.setter
	def money(self, value: float) -> None:
		with self._acting():
			self.household.money = value

	@property
	def concerns(self) -> Any:
		with self._acting():
			return self.household.operating

	@property
	def workforce(self) -> Any:
		with self._acting():
			return self.household.employees

	@property
	def knowledge(self) -> Any:
		with self._acting():
			return self.household.done

	def identity(self) -> str:
		return self.actor_id

	def knows(self, node_id: str, world: Any) -> bool:
		with self._acting():
			return self.household.knows(node_id, world)

	def learn(self, chain: Any, world: Any) -> None:
		with self._acting():
			self.household.done.update(chain)

	def accept_licence(self, node_id: str, chain: Any, world: Any) -> None:
		"""Licensed know-how arrives complete. It was received, not built, so it is held as the society's
		(never counted as the seat's own invention, never lost to a sack)."""
		with self._acting():
			self.household.done.update(chain)
			self.household.granted.update(chain)

	def credit(self, amount: float, purpose: Any) -> None:
		with self._acting():
			self.household.credit(amount, purpose)

	def debit(self, amount: float, purpose: Any) -> None:
		with self._acting():
			self.household.debit(amount, purpose)

	def opened_year_of(self, node_id: str, default: int) -> int:
		with self._acting():
			return self.household.opened_year_of(node_id, default)

	def capacity_of(self, node_id: str) -> float:
		return 1.0
