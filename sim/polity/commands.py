"""Commands to the owner of a seat's standing with its society and state (polity, not moved yet: the bridge applies
them)."""
from dataclasses import dataclass
from typing import Any, Dict

from sim.assembly.api import Command


@dataclass(frozen=True)
class RaiseScandal(Command):
	"""The acting seat's scandal rises by `scandal`, this year's and last year's figure alike."""
	scandal: float


@dataclass(frozen=True)
class RecordBribe(Command):
	"""The acting household's scandal and the year's bribes are set to these figures, and its protection is worked
	out again from them."""
	scandal: float
	bribes_year_to_date: float


@dataclass(frozen=True)
class StrikeFromForce(Command):
	"""`killed` soldiers who died in the field come off the army line of the country `owner`'s state (nothing for an
	owner with no state)."""
	owner: str
	killed: float


@dataclass(frozen=True)
class SetLandTakenMemory(Command):
	"""The state of `owner` remembers the land taken from each tile's people as `by_tile` ({tile: memory})."""
	owner: str
	by_tile: Dict[str, float]


@dataclass(frozen=True)
class RegisterPeople(Command):
	"""The state of `owner` registers its people by tile: each count replaces the one held when it is larger."""
	owner: str
	by_tile: Dict[str, float]


@dataclass(frozen=True)
class SetGrievanceReference(Command):
	"""The level of grievance the state of `owner`'s taxpayers have grown used to."""
	owner: str
	reference: float


@dataclass(frozen=True)
class ResetStateUnrest(Command):
	"""The year's reading of the state of `owner` starts again: no tile has an unrest or a hold figure yet."""
	owner: str


@dataclass(frozen=True)
class SetTileReading(Command):
	"""The year's reading of one tile of the state of `owner`: the unrest of its people and how firmly the state
	holds it (the share of risings its garrison would put down)."""
	owner: str
	tile: str
	unrest: float
	hold: float


@dataclass(frozen=True)
class RecordRising(Command):
	"""A rising on the state of `owner` joins the record of its risings, of which the latest `kept` are kept."""
	owner: str
	entry: Dict[str, Any]
	kept: int


@dataclass(frozen=True)
class ReplaceRuler(Command):
	"""A won rising puts a new ruler of `age` on the throne of `owner`, backed by `backer`, and calls an accession."""
	owner: str
	age: int
	backer: str


@dataclass(frozen=True)
class CloseSuccessionDispute(Command):
	"""The challenger to the succession in the state of `owner` is dropped."""
	owner: str
