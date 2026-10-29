"""Commands to the owner of the cast of other actors and what they are aware of."""
from dataclasses import dataclass
from typing import Any, Optional, Tuple

from sim.assembly.api import Command


@dataclass(frozen=True)
class AdvanceActors(Command):
	"""The year of every actor other than the founder's household: the countries, players, firms, traders and bodies of people
	each decide, pay and post. Coin moved between actors in different places pays carriage meanwhile."""


@dataclass(frozen=True)
class RecordConquestContact(Command):
	"""A conquest of `tile` from `previous` (None when it was nobody's): the conqueror's actors become aware of what the
	overrun country's people know."""
	conqueror: str
	previous: Optional[str]
	tile: str


@dataclass(frozen=True)
class NoteTraderMargin(Command):
	"""A trader actor's last margin changes by `amount` (what its cargo made against what it was booked at). Refused with the
	cause `no_such_actor` when the cast holds no such trader."""
	trader: str
	amount: float


@dataclass(frozen=True)
class RecordMigrantContact(Command):
	"""Migrants moved as `pairs` of (origin tile, destination tile, people): the actors where they arrive become aware of what
	the people of the place they left know."""
	pairs: Tuple[Tuple[str, str, float], ...]


@dataclass(frozen=True)
class ScaleStrata(Command):
	"""Every stratum of the country `country` keeps `1 - share` of its members (a partner's people die by their strata)."""
	country: str
	share: float


@dataclass(frozen=True)
class FollowTileTransfer(Command):
	"""A tile passed from the country `previous` to the country `to_actor` (either may be None or not a country): the countries'
	profiles move it between their home tiles, so their people and taxes pass with it."""
	tile: str
	previous: Optional[str]
	to_actor: Optional[str]


@dataclass(frozen=True)
class SetLenderOffers(Command):
	"""The funds each lender account offers from now on, as (account, amount) pairs in the order the pool keeps them: a lender's
	deposit in the pool moves to what it offers, and an offer of nothing is dropped."""
	offers: Tuple[Tuple[str, float], ...]


@dataclass(frozen=True)
class SettleLenderInterest(Command):
	"""The pool shares the year's interest among its depositors: the actors and seats among them enter it as income, and the
	savers' part is shared among the free strata."""


@dataclass(frozen=True)
class GrantLicence(Command):
    """The acting seat licenses its know-how of `node_id` to `licensee` (a firm, the state or another player) for `fee`, with
    `royalty` a share of the takings. Answers {"status": ...} (see sim/actors/seat_exchange.py)."""
    licensee: Optional[str]
    node_id: str
    fee: float
    royalty: float


@dataclass(frozen=True)
class SellSeatConcern(Command):
    """The acting seat sells a concern it runs to the actor the exchange picks, at the price it sets. Answers {"ok", "buyer",
    "price"} or {"ok": False, "error"}."""
    node_id: str
