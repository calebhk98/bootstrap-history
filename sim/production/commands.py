"""Commands to the owner of what runs and the experience it builds (production, not moved yet: the bridge applies them)."""
from dataclasses import dataclass

from sim.assembly.api import Command


@dataclass(frozen=True)
class AccrueExperience(Command):
	"""Fade every trade's tenure, then add this year's worker-years of running each technique to the industry's experience."""
