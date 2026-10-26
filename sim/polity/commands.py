"""Commands to the owner of a seat's standing with its society and state."""
from dataclasses import dataclass

from sim.assembly.api import Command


@dataclass(frozen=True)
class ChangeStanding(Command):
	"""The acting seat's scandal rises by `scandal` (this year's and last year's figure alike). Other standing fields
	join this command as their writers move."""
	scandal: float = 0.0
