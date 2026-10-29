"""A seat as a party to an exchange.

An exchange handles an actor with `actor_id`, `money`, `concerns`, `knows`, `learn`, `credit`, `debit`,
`opened_year_of`, `capacity_of` and a `record` (stores, offers, opened year, margins, patents, shares). The
seat keeps that state in the modules that own it, so this adapter maps the names onto it: the concerns, opened
years and plants are the seat's business, patents and shares held its stored dealings, and the purse, the
staff and the know-how come through `ports`, the views and commands of their owners (see `SeatPorts`). The
seat's id is the party's `actor_id`.
"""
from typing import Any, ContextManager, Dict, Iterable, Optional, Protocol

from . import business_closing
from .business_plant import Plant
from .records import ActorRecord


class SeatPorts(Protocol):
	"""What a seat's party asks of the rest of the game, for one seat."""

	def acting(self) -> ContextManager[Any]: ...      # the body runs as that seat
	def balance(self) -> float: ...                  # the seat's purse
	def set_balance(self, value: float) -> None: ...
	def credit(self, amount: float, purpose: Any) -> None: ...    # money in or out, entered in the seat's cash book
	def debit(self, amount: float, purpose: Any) -> None: ...
	def note_cash(self, direction: float, amount: float, purpose: Any) -> None: ...   # a posting in the book, entered in the cash book
	def purses(self) -> Any: ...                     # the actors' book the purse is an account in
	def workforce(self) -> Any: ...                  # the seat's people by trade
	def knowledge(self) -> Any: ...                  # the nodes the seat holds
	def receive(self, nodes: Iterable[str], granted: bool) -> None: ...   # know-how handed to the seat complete


class SeatRecord(ActorRecord):
	"""An actor record whose patents, shares and issued equity are the seat's own, so they persist and write through.
	`seat_dealings` is the seat's stored dealings: `patents`, `shares_held`, `shares_issued`, `offers`, `offer_serial`."""

	seat_dealings: Any = None

	@property
	def issued(self) -> float:
		return self.seat_dealings.shares_issued if self.seat_dealings is not None else 0.0

	@issued.setter
	def issued(self, value: float) -> None:
		if self.seat_dealings is not None:
			self.seat_dealings.shares_issued = value

	@property
	def offers(self) -> Any:
		return self.seat_dealings.offers if self.seat_dealings is not None else []

	@offers.setter
	def offers(self, value: Any) -> None:
		if self.seat_dealings is not None:
			self.seat_dealings.offers = value

	@property
	def offer_serial(self) -> int:
		return self.seat_dealings.offer_serial if self.seat_dealings is not None else 0

	@offer_serial.setter
	def offer_serial(self, value: int) -> None:
		if self.seat_dealings is not None:
			self.seat_dealings.offer_serial = value


class HouseholdParty:
	"""Gives a seat the surface an exchange needs; holds no state of its own beyond a transient record."""

	kind = "household"

	def __init__(self, seat_id: str, ports: SeatPorts, margins: Optional[Dict[str, float]] = None, *, dealings: Any, business: Any) -> None:
		"""`dealings` is the seat's stored dealings (`patents`, `shares_held`, `shares_issued`, `offers`, `offer_serial`) and
		`business` the seat's own, the record the ventures module keeps and the exchange opens, closes and hands over plants on."""
		self._ports = ports
		self.actor_id = seat_id
		self._business = business
		self._margins = dict(margins or {})
		self.record = SeatRecord(kind="household", patents=dealings.patents, holdings=dealings.shares_held)
		self.record.seat_dealings = dealings

	@property
	def money(self) -> float:
		return self._ports.balance()

	@money.setter
	def money(self, value: float) -> None:
		self._ports.set_balance(value)

	@property
	def concerns(self) -> Any:
		with self._ports.acting():
			return self._business.operating()

	@property
	def workforce(self) -> Any:
		with self._ports.acting():
			return self._ports.workforce()

	@property
	def knowledge(self) -> Any:
		with self._ports.acting():
			return self._ports.knowledge()

	def identity(self) -> str:
		return self.actor_id

	def knows(self, node_id: str, world: Any) -> bool:
		with self._ports.acting():
			return node_id in self._ports.knowledge() or node_id in world.baseline_knowledge()

	def learn(self, chain: Any, world: Any) -> None:
		with self._ports.acting():
			self._ports.receive(chain, False)

	def accept_licence(self, node_id: str, chain: Any, world: Any) -> None:
		"""Licensed know-how arrives complete. It was received, not built, so it is held as the society's
		(never counted as the seat's own invention, never lost to a sack)."""
		with self._ports.acting():
			self._ports.receive(chain, True)

	@property
	def purses(self) -> Any:
		return self._ports.purses()

	@property
	def account_id(self) -> str:
		return self.actor_id

	def note_income(self, purpose: Any, amount: float) -> None:
		self._ports.note_cash(1.0, amount, purpose)

	def note_outlay(self, purpose: Any, amount: float) -> None:
		self._ports.note_cash(-1.0, amount, purpose)

	def credit(self, amount: float, purpose: Any) -> None:
		self._ports.credit(amount, purpose)

	def debit(self, amount: float, purpose: Any) -> None:
		self._ports.debit(amount, purpose)

	def opened_year_of(self, node_id: str, default: int) -> int:
		with self._ports.acting():
			return self._business.opened_year_of(node_id, default)

	def capacity_of(self, node_id: str) -> float:
		return self._business.size_of(node_id)

	def margin_of(self, node_id: str) -> Any:
		return self._margins.get(node_id)

	def concern_count(self) -> int:
		return 0  # a seat's record keeps no concerns of its own: the household's operating set is the founder's

	def release_plant(self, node_id: str, world: Any) -> Plant:
		with self._ports.acting():
			return business_closing.release_plant(self._business, node_id, world)

	def receive_plant(self, plant: Plant, world: Any) -> None:
		with self._ports.acting():
			self._business.adopt(plant)
