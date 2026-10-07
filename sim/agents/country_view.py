"""`CountryWorld`: the world an actor of another country sees.

Questions about the country (its people, state, techniques, values, government, wages and how much of the
founder's work reaches it) are answered from its profile. Every other member of the shared world passes
straight through, by explicit forwarding methods generated from the `World` protocol at class creation.
"""
import inspect
from typing import Any, Dict, Optional, Set

from .protocols import World
from .records import CountryProfile
from .registry import register_world_scope
from .tuning_country import ARMY_SHARE_OF_POPULATION, COUNTRY_OBSERVATION_RANGE_KM

# members the shared world answers that the protocol does not name yet
EXTRA_FORWARDED: tuple = ()
# the word a civilisation's values use for a weight, as in `w_military`
WEIGHT_PREFIX = "w_"


class _NoGovernment:
	"""Stands in for a government actor the scope was not given: it takes nothing."""

	def collect(self, payer: Any, taxable: float, world: Any) -> float:
		return 0.0


class CountryWorld:
	"""What an actor of `profile`'s country sees. `holder` is the registry (or its saved state)."""

	def __init__(self, shared: Any, profile: CountryProfile, holder: Any) -> None:
		self._shared = shared
		self.profile = profile
		self._holder = holder
		self._baseline: Optional[frozenset] = None

	# ---- the country's own questions
	@property
	def civ_id(self) -> str:
		return self.profile.country

	def baseline_knowledge(self) -> Set[str]:
		if self._baseline is None:
			self._baseline = frozenset(self.profile.starting_techs)
		return self._baseline  # type: ignore[return-value]

	def population_total(self) -> float:
		return self.profile.population

	def urban_population(self) -> float:
		return self.profile.population * self.profile.urban_fraction

	def state_capacity(self) -> float:
		return self.profile.state_capacity

	def tax_share(self) -> float:
		"""Share of its taxpayers' income the country's state starts out taking."""
		return self.profile.tax_share

	def army_wanted(self) -> float:
		declared = self.profile.extra.get("standing_army")
		return float(declared) if declared is not None else self.profile.population * ARMY_SHARE_OF_POPULATION

	def soldiers_under_arms(self) -> float:
		return self.army_wanted()

	def government(self) -> Any:
		"""The country's own government actor; one that takes nothing when the scope was not given a registry."""
		lookup = getattr(self._holder, "government_of", None)
		actor = lookup(self.profile.country) if callable(lookup) else None
		return actor if actor is not None else _NoGovernment()

	def state_weights(self) -> Dict[str, float]:
		"""The shared weights, with the country's own values over them where it declares any."""
		weights = dict(self._shared.state_weights())
		values = self.profile.extra.get("values")
		if isinstance(values, dict):
			for key, weight in values.items():
				if key.startswith(WEIGHT_PREFIX) and isinstance(weight, (int, float)):
					weights[key[len(WEIGHT_PREFIX):]] = float(weight)
		return weights

	def _home_profile(self) -> Optional[CountryProfile]:
		state = getattr(self._holder, "state", self._holder)
		return getattr(state, "countries", {}).get(getattr(state, "home_country", ""))

	def _relative(self, field: str) -> float:
		"""This country's level of a profile figure over the home country's (one when either is unknown)."""
		home = self._home_profile()
		home_level = getattr(home, field, 0.0) if home is not None else 0.0
		own_level = getattr(self.profile, field, 0.0)
		return own_level / home_level if home_level > 0.0 and own_level > 0.0 else 1.0

	def pay_per_person_year(self, trade: str) -> float:
		"""The shared pay scaled by this country's wage level relative to the home country's.

		TEMPORARY HEURISTIC (CLAUDE.md 4.4): a wage computed outside the labour market, because a foreign
		country has no labour market of its own yet (Complaint 407); its output below is scaled alike."""
		return self._shared.pay_per_person_year(trade) * self._relative("wage_index")

	def society_output(self) -> float:
		"""The home society's output per head, scaled by this country's people and its wage level."""
		return self._shared.society_output() * self._relative("population") * self._relative("wage_index")

	def subsistence_cost_per_person_year(self) -> float:
		return self._shared.subsistence_cost_per_person_year() * self._relative("price_index")

	def need_floor_costs_per_person_year(self) -> Dict[str, float]:
		level = self._relative("price_index")
		return {need_id: cost * level for need_id, cost in self._shared.need_floor_costs_per_person_year().items()}

	def exposure(self, node_id: str, location: Optional[str]) -> float:
		"""How much of the founder's work reaches an observer here: the shared visibility, thinned by
		the distance between the observer (the country, when no place is given) and the founder."""
		visibility = self._shared.exposure(node_id, None)
		distance = self._shared.distance_km(location or self.profile.location, None)
		return visibility / (1.0 + distance / COUNTRY_OBSERVATION_RANGE_KM)


def _forward_method(name: str) -> Any:
	def forward(self: CountryWorld, *args: Any, **kwargs: Any) -> Any:
		return getattr(self._shared, name)(*args, **kwargs)
	forward.__name__ = name
	return forward


def _forward_property(name: str) -> property:
	return property(lambda self: getattr(self._shared, name), doc="The shared world's " + name + ".")


def forward_world_member(name: str, is_property: bool = False) -> None:
	"""Pass a shared-world member through, unless CountryWorld answers it itself."""
	if name not in vars(CountryWorld):
		setattr(CountryWorld, name, _forward_property(name) if is_property else _forward_method(name))


for _name, _member in inspect.getmembers(World):
	if not _name.startswith("_") and (isinstance(_member, property) or callable(_member)):
		forward_world_member(_name, isinstance(_member, property))
for _name in EXTRA_FORWARDED:
	forward_world_member(_name)


register_world_scope(lambda world, profile, holder: CountryWorld(world, profile, holder))
