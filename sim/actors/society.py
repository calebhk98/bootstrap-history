"""What the society as a whole knows, as the cast and the acting seat's granted techniques tell it."""
from typing import FrozenSet

from sim.assembly.api import Part

from . import society_rules


class Society(Part):
	"""Needs: techniques_granted."""


	def society_techs(self) -> FrozenSet[str]:
		"""The techniques the society holds now: those granted to the acting seat at the start, and what its firms and government
		have since learnt."""
		actors = []
		if self.parts.cast.cast_recorded():
			registry = self.parts.cast.cast()
			actors = [actor for kind in society_rules.SOCIETY_KINDS for actor in registry.of_kind(kind)]
		return frozenset(society_rules.held_by_society(self.needs.techniques_granted(), actors))
