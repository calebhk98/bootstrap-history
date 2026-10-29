"""A stand-in for the engine that answers for the seats' money with the real ledger over a real book, for tests that need a
seat's purse to move without building a game:

    host = MoneyHost(capital=100.0)
    host.send(CreditSeat("founder", 5.0, "sales"))
    host.view("acting_balance")()   # 105.0

The host holds a `SimulationState` (`host.state`), the actors' book (`host.purses`) and one ledger seat per seat in
`host.state.seats`; `host.port` is what the household facade is built over."""
from typing import Any, Dict

from sim.agents.api import ActorsState
from sim.engine.agents_port_household import SeatMoneyPort
from sim.engine.state import EconomyState, FounderState, HouseholdState, SimulationState
from sim.engine.state_seat import SeatState, bind_seat
from sim.ledger.api import LedgerSeat, OpenCashBook, OpenPurse, RestorePurse
from sim.ledger.ledger import Ledger
from sim.ledger.module_spec import MODULE_SPECS
from sim.tests import module_harness


class MoneyHost:
    def __init__(self, capital: float = 0.0, year: int = 100) -> None:
        self.year = year
        self.state = SimulationState(household=HouseholdState(), economy=EconomyState(), founder=FounderState())
        self.state.actors = ActorsState(home_country="rome_100ad")
        self.purses = self.state.actors.purses
        self.slots: Dict[str, LedgerSeat] = {self.state.acting_seat: LedgerSeat()}
        self.ledger = module_harness.build(Ledger, module_id="ledger", views={
            "cast_state": lambda: self.state.actors, "year": lambda: self.year})
        self.ledger.seat_slot_of = lambda seat_id: self.slots.setdefault(seat_id, LedgerSeat())
        self._handlers = {command_type: getattr(self.ledger, method) for command_type, method in MODULE_SPECS[0].applies}
        self._views = {"acting_balance": self.ledger.acting_balance, "seat_balance": self.ledger.seat_balance,
                       "cash_book": self.ledger.cash_book, "cash_causes_since": self.ledger.cash_causes_since,
                       "cash_unaccounted": self.ledger.cash_unaccounted, "cast_state": lambda: self.state.actors}
        self.port = SeatMoneyPort(self)
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

    def act_as(self, seat_id: str) -> None:
        self._act(seat_id)

    def view(self, name: str) -> Any:
        self._follow_acting_seat()
        return self._views[name]

    def send(self, command: Any) -> Any:
        self._follow_acting_seat()
        return self._handlers[type(command)](command)
