"""Commands to the owner of the seats and the founder's life."""
from dataclasses import dataclass

from sim.assembly.api import Command


@dataclass(frozen=True)
class FounderDies(Command):
	"""The acting seat's run ends for `reason`: the cause of death is set and the log says so."""
	reason: str
