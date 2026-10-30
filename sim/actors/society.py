"""What the society as a whole knows, as the cast and the acting seat's granted techniques tell it."""
from typing import Any, FrozenSet

from . import society_rules


class Society:
	"""Mixed into `Actors`. Needs: techniques_granted."""

	needs: Any

	def society_techs(self) -> FrozenSet[str]:
		"""The techniques the society holds now: those granted to the acting seat at the start, and what its firms and government
		have since learnt."""
		actors = []
		if self.cast_recorded():  # type: ignore[attr-defined]
			registry = self.cast()  # type: ignore[attr-defined]
			actors = [actor for kind in society_rules.SOCIETY_KINDS for actor in registry.of_kind(kind)]
		return frozenset(society_rules.held_by_society(self.needs.techniques_granted(), actors))
