"""What the household facade asks of the engine: the seat's money, answered by the ledger's views and commands."""
from typing import Any

from sim.ledger.api import CreditSeat, DebitSeat, NoteSeatCash, RestorePurse


class SeatMoneyPort:
    """The acting seat's money for the household facade (the facade acts for whichever seat is acting)."""

    def __init__(self, sim: Any) -> None:
        self._sim = sim

    def balance(self) -> float:
        return self._sim.view("acting_balance")()

    def set_balance(self, value: float) -> None:
        self._sim.send(RestorePurse(float(value)))

    def purses(self) -> Any:
        return self._sim.view("cast_state")().purses

    def credit(self, amount: float, purpose: Any) -> None:
        self._sim.send(CreditSeat(self._sim.state.acting_seat, amount, purpose))

    def debit(self, amount: float, purpose: Any) -> None:
        self._sim.send(DebitSeat(self._sim.state.acting_seat, amount, purpose))

    def note_cash(self, direction: float, amount: float, purpose: Any) -> None:
        self._sim.send(NoteSeatCash(self._sim.state.acting_seat, direction, amount, purpose))
