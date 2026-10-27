"""The ledger's commands: every change of a balance is one of these, sent to the ledger."""
from dataclasses import dataclass
from typing import Any, Optional, Tuple

from sim.assembly.api import Command


@dataclass(frozen=True)
class PayEdge(Command):
	"""The acting seat's household pays a named edge (a counterparty the simulation does not model as an actor).
	Never refused for lack of money: a household may go negative, and the credit limit is applied later."""
	edge: str
	amount: float
	purpose: Any                  # a label, or {label: share of the amount}


@dataclass(frozen=True)
class ReceiveFromEdge(Command):
	"""A named edge pays the acting seat's household."""
	edge: str
	amount: float
	purpose: Any


@dataclass(frozen=True)
class PayWages(Command):
	"""The acting seat's household pays wages: the home country's people receive them (the workers edge while there
	are no strata)."""
	amount: float
	purpose: Any


@dataclass(frozen=True)
class ChangeStock(Command):
	"""Tonnes of a commodity (by its commodity key) added to (positive) or taken from (negative) the acting seat's
	stock, counted in this year's opening stock as well, so the year's accounting sees it as held from the start."""
	commodity: str
	tonnes: float
	# Complaint 681, kept until the migration's last equivalence proof: the old living-stock path took the opening
	# snapshot after the change, so the year's first change counts twice in the opening stock
	legacy_snapshot_after_change: bool = False


@dataclass(frozen=True)
class BankStock(Command):
	"""The acting seat's tonnes of each commodity are set to these figures, in order (a later figure for a commodity
	wins). The year's opening snapshot is taken first and not changed: this is what the year's material reading leaves
	of the stock it started from, not a trade."""
	tonnes: Tuple[Tuple[str, float], ...]


@dataclass(frozen=True)
class DrawDownStock(Command):
	"""Tonnes of a commodity (by its commodity key) leave the acting seat's stock, never taking it below zero, as thieves take
	them. The year's opening snapshot is not touched."""
	commodity: str
	tonnes: float


@dataclass(frozen=True)
class NoteSpend(Command):
	"""The acting seat's household counts `amount` in the year's spending, beside the payment that moved it
	(accounting only; applied by the engine bridge until the cash book moves into the ledger)."""
	amount: float


@dataclass(frozen=True)
class PayEdgeFrom(Command):
	"""An actor of the cast (named by its id) pays a named edge. Never refused for lack of money."""
	actor: str
	edge: str
	amount: float
	purpose: Any


@dataclass(frozen=True)
class PayActor(Command):
	"""An actor of the cast (named by its id) pays another party: an actor of the cast, or a seat (named by its seat id,
	paid as that seat's party). A payee that is the government of a country the cast does not hold yet is opened.
	Applied by the engine bridge (the cast and the seats' parties are not the ledger's state yet)."""
	payer: str
	payee: str
	amount: float
	purpose: Any


@dataclass(frozen=True)
class PayActorFromEdge(Command):
	"""A named edge pays an actor of the cast (named by its id). Refused with the cause `no_such_actor` when the cast holds
	no such actor."""
	edge: str
	payee: str
	amount: float
	purpose: Any


# where TakeGoods takes from
STORE_ACTOR = "actor store"       # a material in an actor's own stores (`actor` names it)
STORE_STOCK = "stock ledger"      # a commodity in the acting seat's tonnes ledger
STORE_GRANARY = "granary"         # the acting seat's farm stock, counted in tonnes by the caller


@dataclass(frozen=True)
class TakeGoods(Command):
	"""Tonnes of a good leave a holder's stock (never below zero) and are added to the goods a named edge holds, as
	thieves take them. The holder's opening-stock snapshot is not touched. Applied by the engine bridge (the granary
	and the actors' stores are not the ledger's state yet)."""
	store: str
	good: str
	tonnes: float
	edge: str
	actor: Optional[str] = None


@dataclass(frozen=True)
class PayActorFromHousehold(Command):
	"""The acting seat's household, as a party in the actors' book, pays an actor of the cast (named by its id): one posting
	in the book, entered in the cash book and in the payee's record. Refused with the cause `no_such_actor` when the cast
	holds no such actor."""
	payee: str
	amount: float
	purpose: Any


@dataclass(frozen=True)
class TakeFromHouseholdPurse(Command):
	"""An actor of the cast (named by its id) takes money out of the acting seat's household purse: the purse is debited by
	the figure and the taker credited, as the household's own state does it (not as one posting in the book). Refused with
	the cause `no_such_actor` when the cast holds no such actor."""
	taker: str
	amount: float
	purpose: Any


@dataclass(frozen=True)
class SettleWithEdge(Command):
	"""The acting seat's household is brought to `balance` by moving the difference to or from a named edge."""
	edge: str
	balance: float
	purpose: Any


@dataclass(frozen=True)
class RescaleHouseholdMoney(Command):
	"""The acting seat's purse, and the cash mark its cash book measures from, are multiplied by `ratio`: the money's unit
	changed, nothing was paid."""
	ratio: float


@dataclass(frozen=True)
class WithdrawHouseholdMoney(Command):
	"""The acting seat's household money falls by `amount` with no posting on the ledger's side: the money entered the
	agent economy's own book at the same moment (a bank's capital)."""
	amount: float


@dataclass(frozen=True)
class PayExchange(Command):
    """An actor of the cast (named by its id) puts coin into the exchange edge, to be turned into the economy's unit for a
    purchase: one posting in the actors' book, entered in the actor's outlays under `label`."""
    actor: str
    coin: float
    label: str


@dataclass(frozen=True)
class ReceiveFromExchange(Command):
    """The exchange edge turns the economy's unit back into coin for an actor of the cast (named by its id): one posting in the
    actors' book, entered in the actor's income under `label`."""
    actor: str
    coin: float
    label: str
