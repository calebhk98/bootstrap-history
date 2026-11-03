"""What the actors ask of the country's people: how many, how literate, what a body of them costs to keep."""
from typing import Any, Dict, List, Optional

from sim.agents.api import FOOD_NEED, Hands, observed_incomes
from sim.world import demand, need_basket


class People:
	"""The home country's people and the economy's reading of them. `world` is the root that hands out the parts."""

	def __init__(self, world: Any) -> None:
		self.world = world
		self._countries: Dict[str, Any] = {}

	@property
	def needs(self) -> Any:
		return self.world.needs

	def population_total(self) -> float:
		return self.needs.population_total()

	def urban_population(self) -> float:
		return self.population_total() * self.needs.urban_fraction()

	def subsistence_kg_per_person_year(self) -> float:
		return demand.FOOD_SUBSISTENCE_QUANTITY_KG_PER_CAPITA_PER_YEAR

	def frontier_disease_loss(self) -> float:
		"""The share of working-age people the diseases of the tiles on the frontier take in a year."""
		return self.needs.frontier_disease_loss()

	def country_strata(self) -> List[Any]:
		"""The bodies of people (strata actors) of the state's own country, in id order."""
		return [stratum for stratum in self.world.registry.of_kind("stratum") if stratum.record.country is None]

	def literacy(self, field: str) -> float:
		return self.needs.literacy(field)

	def research_productivity(self, country: Optional[str] = None) -> float:
		return self.needs.research_productivity(country)

	def state_hands(self) -> Any:
		"""The people and food the country can give its state: the working age, the farm hands (the farm
		share of the hours the labour core booked), and the share of the people's food need the last
		year's supply met, with the state's own granary making up what the harvest lacked."""
		needs = self.needs
		farm_hands = needs.working_age() * needs.farm_share_of_hours()     # the labour core's farm share of the hours worked
		last_ratio = needs.nutrition_ratio_last_year()
		ratio = 1.0 if last_ratio is None else last_ratio
		need_tonnes = self.population_total() * self.subsistence_kg_per_person_year() / 1000.0
		granary = self.world.setting.government().record.stores.get(self.world.quotes.staple_material(), 0.0)
		return Hands(needs.working_age(), farm_hands, min(1.0, ratio + (granary / need_tonnes if need_tonnes > 0.0 else 0.0)))

	def need_floor_costs_per_person_year(self) -> Dict[str, float]:
		"""What one person's floor of each need costs a year at the prices households pay: the economy's own
		tile prices on each tile's climate floors (the need-basket kernel, sim/world/need_basket.py). While the
		economy opens, the same kernel on the engine's goods market prices. A need with no priced good is left
		out; with none priced, the food floor is the dole."""
		from_tiles = self.needs.agent_need_floor_costs()
		if from_tiles:
			return from_tiles
		basket = self.needs.household_basket()
		prices = self.needs.household_prices()
		costs = {need.spec.need_id: need.price_index * need.spec.subsistence_per_person
				 for need in need_basket.need_prices(basket, prices.get) if need.spec.subsistence_per_person > 0.0}
		if not costs:
			quotes = self.world.quotes
			tonnes = self.subsistence_kg_per_person_year() / 1000.0
			food_cost = quotes.material_cost(quotes.staple_material(), tonnes)
			if food_cost is not None:
				costs[FOOD_NEED] = food_cost
		return costs

	def country_economy(self, country: str) -> Any:
		"""The agent economy's answers for a partner country that is part of it; None for any other."""
		if country not in self._countries:
			self._countries[country] = self.needs.agent_country[country]
		return self._countries[country]

	def subsistence_cost_per_person_year(self) -> float:
		"""The food floor of `need_floor_costs_per_person_year`."""
		return self.need_floor_costs_per_person_year().get(FOOD_NEED, 0.0)

	def observed_stratum(self, country: Optional[str], name: str) -> Optional[Dict[str, float]]:
		"""The home strata's income from the agent economy's household cohorts (`sim/agents/strata_observed.py`);
		None for another country, or while the economy opens (the strata then keep their own wage bridge)."""
		if country is not None:
			return None
		curve = self.needs.agent_cohort_incomes()
		if not curve:
			return None
		home = [actor for actor in self.world.registry.of_kind("stratum")
				if actor.record.country is None and actor.record.exited_year is None]
		income = observed_incomes(home, self.world, curve).get(name)
		return None if income is None else {"income": income}
