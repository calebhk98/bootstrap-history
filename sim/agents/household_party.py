"""A seat as a party to an exchange.

An exchange handles an actor with `actor_id`, `money`, `concerns`, `knows`, `learn`, `credit`, `debit`,
`opened_year_of`, `capacity_of` and a `record` (stores, offers, opened year, margins, patents, shares). The
seat keeps that state in the modules that own it, so this adapter maps the names onto it through `ports`, the
views and commands of the owners (see `SeatPorts`): the purse, the staff, the know-how, the plants, and the patents,
shares and offers. It holds no record of any of them. The seat's id is the party's `actor_id`.
"""
from typing import Any, ContextManager, Dict, Iterable, Optional, Protocol

from .business_plant import Plant
from .records import ActorRecord
from .tracked import plain, tracked


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
	def dealing(self, field: str) -> Any: ...        # a copy of the seat's stored patents, shares held, shares issued, offers or offer count
	def store_dealing(self, field: str, value: Any) -> None: ...   # the seat's stored figure becomes the one the deal left
	def concerns(self) -> Any: ...                   # the plants the seat runs (read only)
	def opened_year(self, node_id: str, default: int) -> int: ...
	def plant_size(self, node_id: str) -> float: ...
	def release_plant(self, node_id: str, year: int) -> Any: ...  # the plant leaves the seat's business to pass to another owner (None: none)
	def adopt_plant(self, plant: Any) -> None: ...   # the seat's business takes over a plant, with its size and age


class SeatRecord(ActorRecord):
	"""An actor record whose patents, shares and issued equity are the seat's own, kept by the seats module. Each read is a fresh copy of the
	stored figure that reports a change to `ports.store_dealing`, so the exchange changes the record in place, as it does an actor's, and the
	owner is sent the result. `ports` is None until the party attaches them."""

	ports: Any = None

	def _dealing(self, field: str) -> Any:
		if self.ports is None:
			return None
		root: list = []
		root.append(tracked(self.ports.dealing(field), lambda: self.ports.store_dealing(field, plain(root[0]))))
		return root[0]

	def _store(self, field: str, value: Any) -> None:
		if self.ports is not None:
			self.ports.store_dealing(field, plain(value))

	@property
	def patents(self) -> Any:
		return self._dealing("patents") if self.ports is not None else {}

	@patents.setter
	def patents(self, value: Any) -> None:
		self._store("patents", value)

	@property
	def holdings(self) -> Any:
		return self._dealing("shares_held") if self.ports is not None else {}

	@holdings.setter
	def holdings(self, value: Any) -> None:
		self._store("shares_held", value)

	@property
	def issued(self) -> float:
		return self.ports.dealing("shares_issued") if self.ports is not None else 0.0

	@issued.setter
	def issued(self, value: float) -> None:
		self._store("shares_issued", value)

	@property
	def offers(self) -> Any:
		return self._dealing("offers") if self.ports is not None else []

	@offers.setter
	def offers(self, value: Any) -> None:
		self._store("offers", value)

	@property
	def offer_serial(self) -> int:
		return self.ports.dealing("offer_serial") if self.ports is not None else 0

	@offer_serial.setter
	def offer_serial(self, value: int) -> None:
		self._store("offer_serial", value)


class HouseholdParty:
	"""Gives a seat the surface an exchange needs; holds no state of its own beyond a transient record."""

	kind = "household"
	stands_at_home = True   # a seat's purse stands at the home country's centre when coin is carried (sim/coin/carriage.py)

	def __init__(self, seat_id: str, ports: SeatPorts, margins: Optional[Dict[str, float]] = None) -> None:
		self._ports = ports
		self.actor_id = seat_id
		self._margins = dict(margins or {})
		self.record = SeatRecord(kind="household")
		self.record.ports = ports

	@property
	def money(self) -> float:
		return self._ports.balance()

	@money.setter
	def money(self, value: float) -> None:
		self._ports.set_balance(value)

	@property
	def concerns(self) -> Any:
		with self._ports.acting():
			return self._ports.concerns()

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
			return self._ports.opened_year(node_id, default)

	def capacity_of(self, node_id: str) -> float:
		with self._ports.acting():
			return self._ports.plant_size(node_id)

	def margin_of(self, node_id: str) -> Any:
		return self._margins.get(node_id)

	def concern_count(self) -> int:
		return 0  # a seat's record keeps no concerns of its own: the household's operating set is the founder's

	def release_plant(self, node_id: str, world: Any) -> Plant:
		with self._ports.acting():
			plant = self._ports.release_plant(node_id, world.year)
		if plant is None:
			raise KeyError("the business runs no plant of " + node_id)
		return plant

	def receive_plant(self, plant: Plant, world: Any) -> None:
		with self._ports.acting():
			self._ports.adopt_plant(plant)
