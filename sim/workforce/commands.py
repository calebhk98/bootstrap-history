"""Commands to the owner of the labour market and its people."""
from dataclasses import dataclass
from typing import Optional

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
