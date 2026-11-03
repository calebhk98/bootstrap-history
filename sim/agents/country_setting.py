"""What a country's actors see of the setting and of the knowledge: its own civilisation, government, values and techniques."""
from typing import Any, Dict, Optional

from .country_part import SharedPart
from .tuning_country import COUNTRY_OBSERVATION_RANGE_KM

# the word a civilisation's values use for a weight, as in `w_military`
WEIGHT_PREFIX = "w_"


class _NoGovernment:
	"""Stands in for a government actor the scope was not given: it takes nothing."""

	def collect(self, payer: Any, taxable: float, world: Any) -> float:
		return 0.0

	def levy_rates(self) -> Any:
		return 0.0, 0.0


class CountrySetting(SharedPart):
	"""The country's id, its own government and its values over the shared weights."""

	part = "setting"
	# home: the calendar, the map's distances and edges and the nodes are one world's
	home_members = frozenset(("distance_km", "edge", "nodes", "rng_for", "year"))

	@property
	def civ_id(self) -> str:
		return self.world.profile.country

	def government(self) -> Any:
		"""The country's own government actor; one that takes nothing when the country has none."""
		actor = self.world.holder.countries.government_of(self.world.profile.country)
		return actor if actor is not None else _NoGovernment()

	def state_weights(self) -> Dict[str, float]:
		"""The shared weights, with the country's own values over them where it declares any."""
		weights = dict(self.shared.state_weights())
		values = self.world.profile.extra.get("values")
		if isinstance(values, dict):
			for key, weight in values.items():
				if key.startswith(WEIGHT_PREFIX) and isinstance(weight, (int, float)):
					weights[key[len(WEIGHT_PREFIX):]] = float(weight)
		return weights


class CountryKnowledge(SharedPart):
	"""What the country's starting techniques give it, and how much of the founder's work reaches it."""

	part = "knowledge"
	# home: what is known and demonstrated is one body of knowledge; the founder's inventions are the home seat's
	home_members = frozenset(("demonstrated", "founder_inventions", "is_public", "knowledge_half_life_years", "knowledge_visibility"))

	def __init__(self, world: Any) -> None:
		super().__init__(world)
		self._baseline: Optional[frozenset] = None

	def baseline_knowledge(self) -> Any:
		if self._baseline is None:
			self._baseline = frozenset(self.world.profile.starting_techs)
		return self._baseline

	def exposure(self, node_id: str, location: Optional[str]) -> float:
		"""How much of the founder's work reaches an observer here: the shared visibility, thinned by
		the distance between the observer (the country, when no place is given) and the founder."""
		visibility = self.shared.exposure(node_id, None)
		distance = self.world.shared.setting.distance_km(location or self.world.profile.location, None)
		return visibility / (1.0 + distance / COUNTRY_OBSERVATION_RANGE_KM)
