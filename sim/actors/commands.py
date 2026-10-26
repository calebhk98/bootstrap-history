"""Commands to the owner of the cast of other actors and what they are aware of."""
from dataclasses import dataclass
from typing import Optional, Tuple

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
class RecordMigrationContact(Command):
	"""People moved between places, as (origin, destination, people) rows: the actors where they arrive become aware of what
	the people of the place they left know."""
	moves: Tuple[Tuple[str, str, float], ...]


@dataclass(frozen=True)
class NoteTraderMargin(Command):
	"""A trader actor's last margin changes by `amount` (what its cargo made against what it was booked at). Refused with the
	cause `no_such_actor` when the cast holds no such trader."""
	trader: str
	amount: float
