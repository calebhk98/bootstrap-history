"""A stand-in for the game that answers for the seats' money with the real ledger over a real book, for tests that need a seat's
purse to move without building a game:

    host = MoneyHost(capital=100.0)
    host.send(CreditSeat("founder", 5.0, "sales"))
    host.view("acting_balance")()   # 105.0
    party = host.party("founder", dealings=SeatsSeat(), business=Business())   # the seat as an exchange party, over the real ports

The seats' stored dealings and businesses are plain records a test passes to `party`; the party reads them through the owners' views and
changes them through the owners' commands (`SetDealing`, `ReleasePlant`, `AdoptPlant`, applied by the modules' own methods).

The host holds a `SimulationState` (`host.state`), the actors' book (`host.purses`) and one ledger seat per seat in
`host.state.seats`. It is also the `module` the actors' party ports read (`host.needs`, `host.world`): its staff, its know-how and
the know-how handed to it are plain values a test sets."""
import contextlib
from types import SimpleNamespace
from typing import Any, Dict, Iterator

from sim.actors.seat_parties import Ports
from sim.agents.api import ActorsState, HouseholdParty
from sim.agents.tracked import plain
from sim.engine.state import EconomyState, FounderState, HouseholdState, SimulationState
from sim.engine.state_seat import SeatState, bind_seat
from sim.knowledge.api import ReceiveTechniques
from sim.ledger.api import LedgerSeat, OpenCashBook, OpenPurse, RestorePurse
from sim.ledger.ledger import Ledger
from sim.ledger.module_spec import MODULE_SPECS
from sim.seats.dealings import DEALING_FIELDS, Dealings
from sim.seats.api import SetDealing
from sim.ventures.api import AdoptPlant, ReleasePlant
from sim.ventures.module import Ventures
from sim.tests import module_harness


class _Keyed:
    def __init__(self, answer: Any) -> None:
        self._answer = answer

    def __getitem__(self, key: Any) -> Any:
        return self._answer(key)


class MoneyHost:
    def __init__(self, capital: float = 0.0, year: int = 100) -> None:
        self.year = year
        self.state = SimulationState(household=HouseholdState(), economy=EconomyState(), founder=FounderState())
        self.state.actors = ActorsState(home_country="rome_100ad")
        self.world = self.state.actors
        self.purses = self.world.purses
        self.slots: Dict[str, LedgerSeat] = {self.state.acting_seat: LedgerSeat()}
        self.ledger = module_harness.build(Ledger, module_id="ledger", views={
            "cast_state": lambda: self.state.actors, "year": lambda: self.year})
        self.ledger.seat_slot_of = lambda seat_id: self.slots.setdefault(seat_id, LedgerSeat())
        self._handlers = {command_type: getattr(self.ledger, method) for command_type, method in MODULE_SPECS[0].applies}
        self._views = {"acting_balance": self.ledger.acting_balance, "seat_balance": self.ledger.seat_balance,
                       "cash_book": self.ledger.cash_book, "cash_causes_since": self.ledger.cash_causes_since,
                       "cash_unaccounted": self.ledger.cash_unaccounted, "cast_state": lambda: self.state.actors}
        self.employees: Dict[str, float] = {}          # the seats' staff the party reads (one table for every seat)
        self.known: set = set()                       # the nodes the seats hold
        self.received: list = []                      # (nodes, granted) handed to a seat by an exchange
        self.on_receive: Any = None                   # called with (nodes, granted) as the acting seat, when a test keeps the know-how itself
        self.dealings: Dict[str, Any] = {}             # the seats' stored dealings, by seat id (what `party` was given)
        self.businesses: Dict[str, Any] = {}          # the seats' businesses, by seat id
        self.needs = SimpleNamespace(
            send=self.send, seat_balance=_Keyed(lambda seat_id: self.ledger.seat_balance(seat_id)), act_as=self.act_as,
            staff=lambda: {"employees": self.employees}, techniques_held=lambda: self.known,
            seat_dealings=_Keyed(lambda seat_id: {name: plain(getattr(self.dealings[seat_id], name)) for name in DEALING_FIELDS}),
            operating=lambda: self.businesses[self.state.acting_seat].operating(),
            venture_opened_year=lambda node_id, default: self.businesses[self.state.acting_seat].opened_year_of(node_id, default),
            venture_size=_Keyed(lambda node_id: self.businesses[self.state.acting_seat].size_of(node_id)))
        self._act(self.state.acting_seat)
        self.send(RestorePurse(capital))
        self.send(OpenCashBook(capital))

    def _act(self, seat_id: str) -> None:
        bind_seat(self.state, seat_id)
        self._follow_acting_seat()

    def _follow_acting_seat(self) -> None:
        """The ledger answers for the seat that is acting now, however a test switched to it."""
        acting = self.state.acting_seat
        self.ledger.clock.act_as(acting)
        self.ledger.seat = self.ledger.seat_slot_of(acting)

    def add_seat(self, seat_id: str, capital: float = 0.0) -> None:
        """A second seat holding `capital`; the acting seat stays as it was."""
        acting = self.state.acting_seat
        self.state.seats[seat_id] = SeatState(household=HouseholdState(), founder=FounderState())
        self.send(OpenPurse(seat_id, capital))
        self._act(acting)

    @contextlib.contextmanager
    def act_as(self, seat_id: str) -> Iterator[Any]:
        """Run the body as `seat_id`, then restore the seat that was acting."""
        previous = self.state.acting_seat
        self._act(seat_id)
        try:
            yield self
        finally:
            self._act(previous)

    def party(self, seat_id: str, margins: Any = None, *, dealings: Any, business: Any) -> HouseholdParty:
        """`seat_id` as a party to an exchange, over the actors' own ports; `dealings` and `business` are the records its owners keep."""
        self.dealings[seat_id], self.businesses[seat_id] = dealings, business
        return HouseholdParty(seat_id, Ports(self, seat_id), margins)

    def view(self, name: str) -> Any:
        self._follow_acting_seat()
        return self._views[name]

    def send(self, command: Any) -> Any:
        self._follow_acting_seat()
        if isinstance(command, ReceiveTechniques):
            self.received.append((tuple(command.node_ids), command.granted))
            if self.on_receive is None:
                self.known.update(command.node_ids)
            else:
                self.on_receive(command.node_ids, command.granted)
            return None
        if isinstance(command, SetDealing):
            return Dealings.set_dealing(SimpleNamespace(_slots=lambda: self.dealings), command)
        if isinstance(command, (ReleasePlant, AdoptPlant)):
            owner = SimpleNamespace(seat_of=lambda seat_id: SimpleNamespace(business=self.businesses[seat_id]))
            return (Ventures.apply_release_plant if isinstance(command, ReleasePlant) else Ventures.apply_adopt_plant)(owner, command)
        return self._handlers[type(command)](command)
