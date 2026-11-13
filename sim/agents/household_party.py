"""A seat as a party to an exchange.

An exchange handles an actor with `actor_id`, `money`, `concerns`, `knows`, `learn`,
`holdings` (`opened_year_of`, `capacity_of`, ...), `payments` (`credit`, `debit`, `note_income`, `note_outlay`) and a `record` (stores, offers, opened year, margins, patents, shares). The
seat keeps that state in the modules that own it, so this adapter maps the names onto it through `ports`, the
views and commands of the owners (see `SeatPorts`): the purse, the staff, the know-how, the plants, and the patents,
shares and offers. It holds no record of any of them. The seat's id is the party's `actor_id`.
"""
from typing import Any, ContextManager, Dict, Iterable, Optional, Protocol

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
	def dealing(self, field: str) -> Any: ...        # a copy of the seat's stored patents, shares held, shares issued, offers or offer count
	def release_patent(self, node_id: str, taker_id: str) -> Any: ...   # each of these sends the seats module the matching command (sim/seats/commands.py)
	def receive_patent(self, node_id: str, entry: Any) -> None: ...
	def add_licensee(self, node_id: str, licensee_id: str) -> None: ...
	def give_shares(self, issuer_id: str, share: float, own_issue: bool) -> None: ...
	def take_shares(self, issuer_id: str, share: float, own_issue: bool) -> None: ...
	def keep_offer(self, offer: Any) -> None: ...
	def drop_offer(self, offer_id: str) -> None: ...
	def drop_lapsed_offers(self, year: int) -> Any: ...
	def next_offer_serial(self) -> int: ...
	def concerns(self) -> Any: ...                   # the plants the seat runs (read only)
	def opened_year(self, node_id: str, default: int) -> int: ...
	def plant_size(self, node_id: str) -> float: ...
	def release_plant(self, node_id: str, year: int) -> Any: ...  # the plant leaves the seat's business to pass to another owner (None: none)
	def adopt_plant(self, plant: Any) -> None: ...   # the seat's business takes over a plant, with its size and age


class SeatRecord(ActorRecord):
	"""An actor record whose patents, shares and issued equity are the seat's own, kept by the seats module. Each read is a fresh copy of the
	stored figure; each change the exchange makes (`release_patent`, `give_shares`, `keep_offer`, ...) is the matching command to the owner,
	which applies the same rule (`dealing_figures.py`) to its figure. `ports` is None until the party attaches them."""

	ports: Any = None

	def _read(self, field: str, empty: Any) -> Any:
		return self.ports.dealing(field) if self.ports is not None else empty

	def _refuse_write(self) -> None:
		if self.ports is not None:
			raise AttributeError("a seat's dealings change by the seats module's commands, not by assignment")

	@property
	def patents(self) -> Any:
		return self._read("patents", {})

	@patents.setter
	def patents(self, value: Any) -> None:
		self._refuse_write()

	@property
	def shares_held(self) -> Any:
		return self._read("shares_held", {})

	@shares_held.setter
	def shares_held(self, value: Any) -> None:
		self._refuse_write()

	@property
	def issued(self) -> float:
		return self._read("shares_issued", 0.0)

	@issued.setter
	def issued(self, value: float) -> None:
		self._refuse_write()

	@property
	def offers(self) -> Any:
		return self._read("offers", [])

	@offers.setter
	def offers(self, value: Any) -> None:
		self._refuse_write()

	@property
	def offer_serial(self) -> int:
		return self._read("offer_serial", 0)

	@offer_serial.setter
	def offer_serial(self, value: int) -> None:
		self._refuse_write()

	def release_patent(self, node_id: str, taker_id: str) -> Any:
		return self.ports.release_patent(node_id, taker_id)

	def receive_patent(self, node_id: str, entry: Any) -> None:
		self.ports.receive_patent(node_id, entry)

	def add_licensee(self, node_id: str, licensee_id: str) -> None:
		self.ports.add_licensee(node_id, licensee_id)

	def give_shares(self, issuer_id: str, share: float, own_issue: bool) -> None:
		self.ports.give_shares(issuer_id, share, own_issue)

	def take_shares(self, issuer_id: str, share: float, own_issue: bool) -> None:
		self.ports.take_shares(issuer_id, share, own_issue)

	def keep_offer(self, offer: Any) -> None:
		self.ports.keep_offer(offer)

	def drop_offer(self, offer_id: str) -> None:
		self.ports.drop_offer(offer_id)

	def drop_lapsed_offers(self, year: int) -> Any:
		return self.ports.drop_lapsed_offers(year)

	def next_offer_serial(self) -> int:
		return self.ports.next_offer_serial()


class HouseholdHoldings:
	"""The seat's plants as the exchange reads them (`party.holdings`), through the seat's ports. Only the members the exchange needs are here; `staffed_share` is firm-only (a
	seat's crew is the founder's staff, not a plant's), and its callers are firm code."""

	def __init__(self, ports: SeatPorts, margins: Dict[str, float]) -> None:
		self.ports = ports
		self.margins = margins

	def opened_year_of(self, node_id: str, default: int) -> int:
		with self.ports.acting():
			return self.ports.opened_year(node_id, default)

	def capacity_of(self, node_id: str) -> float:
		with self.ports.acting():
			return self.ports.plant_size(node_id)

	def margin_of(self, node_id: str) -> Any:
		return self.margins.get(node_id)

	def concern_count(self) -> int:
		return 0  # a seat's record keeps no concerns of its own: the household's operating set is the founder's

	def release_plant(self, node_id: str, world: Any) -> Plant:
		with self.ports.acting():
			plant = self.ports.release_plant(node_id, world.setting.year)
		if plant is None:
			raise KeyError("the business runs no plant of " + node_id)
		return plant

	def receive_plant(self, plant: Plant, world: Any) -> None:
		with self.ports.acting():
			self.ports.adopt_plant(plant)


class HouseholdPayments:
	"""The seat's money moves (`party.payments`): each is a command to the owner of the seat's cash book."""

	def __init__(self, ports: SeatPorts) -> None:
		self.ports = ports

	def note_income(self, purpose: Any, amount: float) -> None:
		self.ports.note_cash(1.0, amount, purpose)

	def note_outlay(self, purpose: Any, amount: float) -> None:
		self.ports.note_cash(-1.0, amount, purpose)

	def credit(self, amount: float, purpose: Any) -> None:
		self.ports.credit(amount, purpose)

	def debit(self, amount: float, purpose: Any) -> None:
		self.ports.debit(amount, purpose)


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
		self.holdings = HouseholdHoldings(ports, self._margins)
		self.payments = HouseholdPayments(ports)

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
			return node_id in self._ports.knowledge() or node_id in world.knowledge.baseline_knowledge()

	def imitation_worth(self, node_id: str, world: Any) -> float:
		"""A seat's worth of an invention is the player's to judge, as a player actor's is: nothing here."""
		return 0.0

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
