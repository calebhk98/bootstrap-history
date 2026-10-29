"""Commands to the owner of the labour market and its people."""
from dataclasses import dataclass
from typing import Dict, Optional

from sim.assembly.api import Command


@dataclass(frozen=True)
class PressLabour(Command):
	"""Record demand for `hours` a year of a trade that is not a hire, which raises that trade's wage pressure."""
	trade: str
	hours: float


@dataclass(frozen=True)
class SetEmployed(Command):
	"""The acting seat's staff in `trade` become `headcount` full-time equivalents, and the hour pools follow."""
	trade: str
	headcount: float


@dataclass(frozen=True)
class NoteTradeSpread(Command):
	"""The acting seat's record of a taught trade: the year it was first seen taught (`introduced_year`, when
	given) and whether it has become endemic to the society (`endemic`, when true)."""
	trade: str
	introduced_year: Optional[int] = None
	endemic: bool = False


@dataclass(frozen=True)
class SurviveStaff(Command):
	"""Each person on the acting seat's books survives with probability `survival_share`, rolled one by one so
	headcounts stay whole; a trade left with nobody is dropped. Draws from the game's dice."""
	survival_share: float


@dataclass(frozen=True)
class GrantStaff(Command):
	"""An institution hands the acting seat people outright, on completion: recorded as a grant, so the yearly resync of
	the pools from the payroll keeps them."""
	scholars: float = 0.0
	artisans: float = 0.0


@dataclass(frozen=True)
class ScaleDeputies(Command):
	"""The acting seat's pool of deputy directors is multiplied by `share`."""
	share: float


@dataclass(frozen=True)
class ReportStaffReduction(Command):
	"""The acting seat's log says which trades have fewer people than the headcount `before` ({trade: headcount}), and
	that `cause` is why."""
	cause: str
	before: Dict[str, float]


@dataclass(frozen=True)
class ReleaseStaff(Command):
	"""`people` of a trade leave the payroll of the seat `seat_id` and go back to the pool the labour market draws on."""
	seat_id: str
	trade: str
	people: float


@dataclass(frozen=True)
class AllocateFarmWorkforce(Command):
	"""The society's farm workforce for a year is sized for a people of `adult_equivalent_population`, the year's farming
	technique is chosen and the farm's hours needed are set. Answers the full-time equivalents on the farm."""
	adult_equivalent_population: float


@dataclass(frozen=True)
class ApplyLandClearing(Command):
	"""Hands beyond what the farm can crop spent the year clearing: the farm area grows by what they cleared."""


@dataclass(frozen=True)
class UpdateWages(Command):
	"""One year of wage adjustment toward the trades that are short."""


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
