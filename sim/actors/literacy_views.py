"""The reading shares of a country: what its strata hold, and the teaching that moves them."""
from typing import Any, Dict, Optional, Sequence, Tuple

from sim.assembly.api import Part

from . import country_rules, literacy_rules


class LiteracyViews(Part):
	"""The strata are founded by the first question about a country's reading."""

	def country_literacy_figure(self, country: Optional[str], field: str) -> float:
		"""The share of the country's people (the home country when None) who read, general or elite."""
		return country_rules.country_literacy(self.parts.cast.seeded_actor_registry(), country).get(field)

	def country_literacy_ceiling(self, country: Optional[str], common: float, propertied: float) -> float:
		"""The national ceiling: each group's own limit weighted by its members."""
		return country_rules.country_literacy(self.parts.cast.seeded_actor_registry(), country).ceiling(common, propertied)

	def literacy_after_schooling(self, country: Optional[str], steps: Sequence[Tuple[str, float, float]]) -> Tuple[Dict[str, float], Dict[str, float]]:
		"""The figures before and after the schools' steps, tried on a copy: no stratum changes."""
		literacy = country_rules.country_literacy(self.parts.cast.seeded_actor_registry(), country).copy()
		return literacy_rules.school(literacy, steps)

	def teach_literacy(self, command: Any) -> None:
		"""Research teaches the home country's people toward `command.value`, bounded by `command.ceiling`."""
		country_rules.country_literacy(self.parts.cast.seeded_actor_registry(), None).teach(command.field, command.value, command.ceiling)

	def school_literacy(self, command: Any) -> Tuple[Dict[str, float], Dict[str, float]]:
		"""The schools close the gaps in the home country's strata. Answers the figures before and after."""
		return literacy_rules.school(country_rules.country_literacy(self.parts.cast.seeded_actor_registry(), None), command.steps)
