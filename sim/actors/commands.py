"""Commands to the owner of the cast of other actors and what they are aware of."""
from dataclasses import dataclass
from typing import Optional, Tuple

from sim.assembly.api import Command


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
