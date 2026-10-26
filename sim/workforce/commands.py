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
class NoteWageShock(Command):
	"""The acting seat's cause book records that a shock named `cause` moved the wage index from `index_before` to what
	it is now."""
	cause: str
	index_before: float
