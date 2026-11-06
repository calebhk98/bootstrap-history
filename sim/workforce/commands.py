"""Commands to the owner of the labour market and its people."""
from dataclasses import dataclass
from typing import Any, Optional

from sim.assembly.api import Command


@dataclass(frozen=True)
class SetEmployed(Command):
	"""The acting seat's staff in `trade` become `headcount` full-time equivalents, and the hour pools follow."""
	trade: str
	headcount: float


@dataclass(frozen=True)
class StaffArrived(Command):
	"""The acting seat's staff in `trade` are the `people` the labour core's clearing hired for it; the standing bid stays."""
	trade: str
	people: float


@dataclass(frozen=True)
class HoursArrived(Command):
	"""The labour core's clearing filled the acting seat's one-year order of a purpose: `hours_by_trade` are the hours hired
	(a commission's become its contract hours). The order is spent either way."""
	purpose: str
	hours_by_trade: Any


@dataclass(frozen=True)
class PostHoursOnce(Command):
	"""The acting seat asks the labour core for `hours` more of `trade` this year only, for a purpose. Answers nothing."""
	purpose: str
	trade: str
	hours: float


@dataclass(frozen=True)
class NoteTradeSpread(Command):
	"""The acting seat's record of a taught trade: the year it was first seen taught (`introduced_year`, when
	given) and whether it has become endemic to the society (`endemic`, when true)."""
	trade: str
	introduced_year: Optional[int] = None
	endemic: bool = False


@dataclass(frozen=True)
class ClearingSettled(Command):
	"""The year's clearing charged the acting seat `wages_charged` for its staff and one-year orders and paid it `wage_work_pay`
	for the hours of its own it offered in the labour market (both in money); the offers are spent."""
	wages_charged: float
	wage_work_pay: float


@dataclass(frozen=True)
class NewcomersPlaced(Command):
	"""The acting seat's newly trained and granted people were put into the labour core; the list of them is spent."""


@dataclass(frozen=True)
class NoteClearedWage(Command):
	"""The year's clearing set the unskilled hour's wage at `wage` (None: no market cleared one); the last reading becomes the one before."""
	wage: Optional[float]


@dataclass(frozen=True)
class GrantStaff(Command):
	"""An institution hands the acting seat people outright, on completion: they join the seat's staff and the labour core,
	and are hired at the clearing like anyone."""
	scholars: float = 0.0
	artisans: float = 0.0


@dataclass(frozen=True)
class LoseStaff(Command):
	"""A shock takes people from the acting seat: the people on its books are scaled by `survival_share`, fractions kept
	(a trade left with nobody is dropped), its pool of deputy
	directors is multiplied by `deputies_share`, and its log says which trades fell and that `cause` is why. Answers
	{"people_before": ..., "people_after": ...}, the scholars, artisans and hired people on the books either side."""
	cause: str
	survival_share: float
	deputies_share: float


@dataclass(frozen=True)
class ReleaseStaff(Command):
	"""`people` of a trade leave the payroll of the seat `seat_id` and go back to the pool the labour market draws on."""
	seat_id: str
	trade: str
	people: float


@dataclass(frozen=True)
class BuildHousing(Command):
	"""The acting seat's household pays for `places` of worker housing, if its capital covers them. Answers the places
	built, nothing when the capital does not cover them."""
	places: float


@dataclass(frozen=True)
class TakeWageFallback(Command):
	"""The acting seat has `remaining_hours` of its year unspent. When the household has no work and thin means it sells
	hours for wages (unless the seat is played by hand). Answers the hours still unspent."""
	remaining_hours: float


@dataclass(frozen=True)
class CloseHoursYear(Command):
	"""The acting seat's year of hours ends: where they went is kept as last year's breakdown (`pool` was the year's project
	budget, `remaining` the hours left unspent, `remaining_after_projects` what was left once the projects had theirs and
	`hours_effective_total` what actually reduced the projects' founder hours), the wage ledger is closed and the year's
	hour tallies and contracted work reset."""
	pool: float
	remaining: float
	remaining_after_projects: float
	hours_effective_total: float
