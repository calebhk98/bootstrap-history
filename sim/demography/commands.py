"""Commands to the owner of the people of each country."""
from dataclasses import dataclass

from sim.assembly.api import Command


@dataclass(frozen=True)
class AddCaptives(Command):
	"""`people` taken in war join the bonded stratum of the country `winner`, where it has one. Answers the people added
	(zero where the country has no bonded stratum)."""
	winner: str
	people: float
