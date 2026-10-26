"""Commands to the owner of the labour market and its people."""
from dataclasses import dataclass

from sim.assembly.api import Command


@dataclass(frozen=True)
class PressLabour(Command):
	"""Record demand for `hours` a year of a trade that is not a hire, which raises that trade's wage pressure."""
	trade: str
	hours: float
