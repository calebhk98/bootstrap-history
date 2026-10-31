"""The seats as actors of the exchange: each seat, as the actors' book and the exchange deal with it, built here from the views and
commands of the modules that own what a seat holds.

A seat's money is the ledger's (its view `seat_balance`, its commands that move the purse and enter the cash book), its staff the
workforce's, its know-how the knowledge module's, its plants the ventures module's and its patents, shares and offers the seats
module's. The party an exchange or a lender deals with is built from those for the length of one dealing and handed to no other
module. It holds no record of the seat's dealings or business: it reads them from their owners and sends them what a deal changed."""
from typing import Any, ContextManager, Dict, Iterable, Optional

from sim.agents.api import HouseholdParty
from sim.knowledge.api import ReceiveTechniques
from sim.ledger.api import CreditSeat, DebitSeat, NoteSeatCash, RestorePurse
from sim.seats.api import SetDealing
from sim.ventures.api import AdoptPlant, ReleasePlant


class Ports:
    """What one seat's party asks of the game (`sim.agents.api.SeatPorts`): the owners' views and commands, naming the seat."""

    def __init__(self, module: Any, seat_id: str) -> None:
        self._module, self._seat_id = module, seat_id

    @property
    def _needs(self) -> Any:
        return self._module.needs

    def acting(self) -> ContextManager[Any]:
        return self._needs.act_as(self._seat_id)

    def balance(self) -> float:
        return self._needs.seat_balance[self._seat_id]

    def set_balance(self, value: float) -> None:
        self._needs.send(RestorePurse(float(value), self._seat_id))

    def credit(self, amount: float, purpose: Any) -> None:
        self._needs.send(CreditSeat(self._seat_id, amount, purpose))

    def debit(self, amount: float, purpose: Any) -> None:
        self._needs.send(DebitSeat(self._seat_id, amount, purpose))

    def note_cash(self, direction: float, amount: float, purpose: Any) -> None:
        self._needs.send(NoteSeatCash(self._seat_id, direction, amount, purpose))

    def purses(self) -> Any:
        return self._module.world.purses

    def workforce(self) -> Any:
        return self._needs.staff()["employees"]

    def knowledge(self) -> Any:
        return self._needs.techniques_held()

    def receive(self, nodes: Iterable[str], granted: bool) -> None:
        self._needs.send(ReceiveTechniques(tuple(nodes), granted, self._needs.year()))

    def dealing(self, field: str) -> Any:
        return self._needs.seat_dealings[self._seat_id][field]

    def store_dealing(self, field: str, value: Any) -> None:
        self._needs.send(SetDealing(self._seat_id, field, value))

    def concerns(self) -> Any:
        return self._needs.operating()

    def opened_year(self, node_id: str, default: int) -> int:
        return self._needs.venture_opened_year(node_id, default)

    def plant_size(self, node_id: str) -> float:
        return self._needs.venture_size[node_id]

    def release_plant(self, node_id: str, year: int) -> Any:
        return self._needs.send(ReleasePlant(self._seat_id, node_id, year))

    def adopt_plant(self, plant: Any) -> None:
        self._needs.send(AdoptPlant(self._seat_id, plant))


class SeatParties:
    """Mixed into `Actors`."""

    needs: Any
    world: Any

    def seat_party(self, seat_id: str, margins: Optional[Dict[str, float]] = None) -> HouseholdParty:
        """`seat_id` as an actor an exchange can deal with: it holds patents and shares, pays and is paid."""
        return HouseholdParty(seat_id, Ports(self, seat_id), margins)

    def seat_parties(self) -> Dict[str, HouseholdParty]:
        """Every seat that has joined as an actor, by seat id: the founder and other players hold patents and shares."""
        return {seat_id: self.seat_party(seat_id) for seat_id in self.needs.seat_list()["joined"]}

    def find_dealer(self, actor_id: Any) -> Any:
        """The actor with this id: a seat that has joined, else one in the registry."""
        if isinstance(actor_id, str) and actor_id in self.needs.seat_list()["joined"]:
            return self.seat_party(actor_id)
        return self.cast().get(actor_id) if isinstance(actor_id, str) else None
