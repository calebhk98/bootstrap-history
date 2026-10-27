"""Commands the screens send to change the acting seat's people, hours and base. Each answers what the labour model answers:
a (result, error) pair, or the count."""
from dataclasses import dataclass
from typing import Any, Optional

from sim.assembly.api import Command


@dataclass(frozen=True)
class HireStaff(Command):
	"""Hire `count` people of `trade` at the market's price. Answers (hired, error)."""
	trade: Any
	count: Any


@dataclass(frozen=True)
class FireStaff(Command):
	"""Let `count` people of `trade` go. Answers (fired, error)."""
	trade: Any
	count: Any


@dataclass(frozen=True)
class TrainStaff(Command):
	"""Teach `count` people `trade`, from the trade `source` (None: the nearest the society teaches). Answers (trained, message)."""
	trade: Any
	count: Any
	source: Optional[str] = None


@dataclass(frozen=True)
class CommissionHours(Command):
	"""Buy `hours` of `trade` for this year only. Answers (commissioned, message)."""
	trade: Any
	hours: Any


@dataclass(frozen=True)
class WorkForWages(Command):
	"""The acting seat sells `hours` of its own time as `trade` this year. Answers (pay, message)."""
	trade: Any
	hours: Any


@dataclass(frozen=True)
class BuySlaves(Command):
	"""Buy `people` enslaved people. Answers how many were bought."""
	people: int


@dataclass(frozen=True)
class Manumit(Command):
	"""Free `people` enslaved people. Answers how many were freed."""
	people: int


@dataclass(frozen=True)
class FoundTradeSchool(Command):
	"""Found a school of `trade` with `seats` places. Answers (founded, why not)."""
	trade: Any
	seats: Any


@dataclass(frozen=True)
class MoveBase(Command):
	"""Move the household to `tile`, one the nation holds. Answers (moved, message)."""
	tile: Any
