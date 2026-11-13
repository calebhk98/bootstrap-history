"""What a country's actors see of its people: their number, literacy, hands and what a body of them costs to keep."""
from typing import Any, Dict, List

from .country_hands import hands_of
from .country_part import SharedPart
from .country_population import people_counted
from .literacy import CountryLiteracy
from .stratum_year import FOOD_NEED


class CountryPeople(SharedPart):
	"""The country's people, from its profile and its own part of the economy."""

	part = "people"
	# home: a person's subsistence is a physical figure; the economy and strata lookups are the shared people's
	home_members = frozenset(("country_economy", "observed_stratum", "subsistence_kg_per_person_year"))

	def population_total(self) -> float:
		return people_counted(self.world.profile)

	def urban_population(self) -> float:
		return people_counted(self.world.profile) * self.world.profile.urban_fraction

	def country_strata(self) -> List[Any]:
		holder = self.world.holder
		state = holder.state
		home = state.home_country
		return [actor for actor in holder.of_kind("stratum")
				if (actor.record.country or home) == self.world.profile.country]

	def literacy(self, field: str) -> float:
		return CountryLiteracy(self.country_strata()).get(field)

	def urban_mortality_premium(self) -> None:
		"""A country does not follow its towns' mortality: no figure."""
		return None

	def frontier_disease_loss(self) -> None:
		"""A country does not follow its regions' disease: no figure."""
		return None

	def research_productivity(self) -> float:
		return self.shared.research_productivity(self.world.profile.country)

	def state_hands(self) -> Any:
		"""The people and food this country can give its state (country_hands.py)."""
		return hands_of(self.world.profile)

	def need_floor_costs_per_person_year(self) -> Dict[str, float]:
		"""The country's floor of each need at its own prices."""
		own = self.world.own
		return own.answer("need floors", own.get().need_floor_costs_per_person_year())

	def subsistence_cost_per_person_year(self) -> float:
		"""The country's food floor at its own prices."""
		return self.world.own.answer("food floor", self.need_floor_costs_per_person_year().get(FOOD_NEED))
