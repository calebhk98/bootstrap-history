"""Commands to the owner of a seat's standing with its society and state (polity, not moved yet: the bridge applies
them)."""
from dataclasses import dataclass

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
