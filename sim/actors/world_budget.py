"""What a state asks the simulated world when it budgets: its people, its prices, its taxpayers."""
from typing import Any, List, Optional, Tuple

from sim.agents.api import DOLE_MATERIAL, Hands, army_goal, sack_pressure, taxpayer_income
from sim.world import agriculture, demand
from sim.geography.api import territory


class BudgetView:
	"""Read-only questions behind a state's standing need; mixed into `ActorWorld`."""

	needs: Any
	registry: Any

	def population_total(self) -> float:
		return self.needs.population_total()

	def state_reach(self) -> float:
		return self.needs.state_authority()

	def territory(self) -> Any:
		"""Frontier, coast and road length of the tiles the state holds."""
		return territory.holdings(self.needs.home_tiles_held())

	def frontier_disease_loss(self) -> float:
		"""The share of working-age people the diseases of the tiles on the frontier take in a year."""
		return self.needs.frontier_disease_loss()

	def country_strata(self) -> List[Any]:
		"""The bodies of people (strata actors) of the state's own country, in id order."""
		return [stratum for stratum in self.registry.of_kind("stratum") if stratum.record.country is None]

	def literacy(self, field: str) -> float:
		return self.needs.literacy(field)

	def research_productivity(self, country=None) -> float:
		return self.needs.research_productivity(country)

	def urban_population(self) -> float:
		return self.population_total() * self.needs.urban_fraction()

	def subsistence_kg_per_person_year(self) -> float:
		return demand.FOOD_SUBSISTENCE_QUANTITY_KG_PER_CAPITA_PER_YEAR

	def national_people(self, trade: str) -> float:
		"""People of a trade in the whole country; the working age for unskilled labour."""
		return self.needs.working_age() if trade == "labourer" else self.needs.trade_population[trade]

	def trade_exists(self, trade: str) -> bool:
		return self.needs.trade_available[trade]

	def threat_pressure(self) -> float:
		"""Probability a year of the civilisation's own hazards sack a site: the declared
		sack chances of those running now, before any relief the founder has bought."""
		return sack_pressure(self.needs.civilisation().get("hazards", []), self.year)

	def army_wanted(self) -> float:
		"""Soldiers the state wants: the opening force the civilisation starts with, raised by the
		threat its hazards describe. The garrison follows the frontier, not the head count."""
		opening = float(self.needs.civilisation().get("standing_army", 0.0))
		return army_goal(opening, self.threat_pressure())

	def soldiers_under_arms(self) -> float:
		"""Soldiers the state keeps now: what it paid for last year, else the force it wants."""
		kept = self.government().record.army
		return kept if kept > 0.0 else self.army_wanted()

	def state_hands(self) -> Any:
		"""The people and food the country can give its state: the working age, the farm hands the society's
		farming wants (none known before its first allocation), and the share of the people's food need the last
		year's supply met, with the state's own granary making up what the harvest lacked."""
		needs = self.needs
		hours = needs.farm_holdings()["hours_needed"]
		farm_hands = 0.0 if hours is None else hours / agriculture.ANNUAL_LABOUR_HOURS_PER_FARM_WORKER
		last_ratio = needs.nutrition_ratio_last_year()
		ratio = 1.0 if last_ratio is None else last_ratio
		need_tonnes = self.population_total() * self.subsistence_kg_per_person_year() / 1000.0
		granary = self.government().record.stores.get(DOLE_MATERIAL, 0.0)
		return Hands(needs.working_age(), farm_hands, min(1.0, ratio + (granary / need_tonnes if need_tonnes > 0.0 else 0.0)))

	def patron_ask(self) -> float:
		return self.needs.patron_funding_ask()

	def equipment_kg_per_soldier(self) -> float:
		"""Iron and ammunition one equipped soldier uses a year, at the equipment the state's
		armies have taken up from the founder's work."""
		return self.needs.military_equipment_burden(self.needs.state_military_diffusion())

	def military_work_ids(self) -> Tuple[str, ...]:
		return tuple(self.needs.diffusible_ids["military"])

	def equipment_kg_at_adoption(self, adoption: float) -> float:
		return self.needs.military_equipment_burden(adoption)

	def pay_per_person_year(self, trade: str) -> float:
		return self.labour_market.quote_annual(trade)  # type: ignore[attr-defined]

	def commodity_of(self, material: str) -> str:
		return self.needs.material_commodity[material]

	def material_cost(self, material: str, tonnes: float) -> Optional[float]:
		"""Money to buy this many tonnes of a material at the price the market quotes; None when nothing sells it."""
		quote = self.needs.material_purchase_cost(material, tonnes)
		return None if quote is None else quote[0]

	def fleet_goods(self, holder_id: Optional[str] = None) -> List[Any]:
		"""Available naval vessels, their crews, service lives and a state's holdings (the founder's state's by default)."""
		return self.needs.fleet_goods(holder_id or self.government().actor_id)

	def local_staff(self, trade: str, people: float) -> float:
		"""How many of `people` kept in a trade nationwide come out of the founder's own labour
		market: the share of the nation's people of that trade they are, applied to the pool the
		founder can reach. Unskilled labour is the whole working age."""
		nation = self.national_people(trade)
		if nation <= 0.0:
			return 0.0
		reach = self.needs.reachable_trade_population[trade] + self.module.actor_staff_fte(trade)
		return min(1.0, people / nation) * reach

	def notice_over(self, scale: float, capacity: Optional[float] = None) -> float:
		return self.needs.notice_over(scale, capacity)

	def seat_taxpayers(self, country: Optional[str]) -> List[Tuple[float, float]]:
		"""(visible scale, taxable income) of the playing household seats that belong to `country`; a seat with no
		country belongs to the game's own (home) country."""
		needs = self.needs
		home = self.registry.state.home_country
		payers = []
		for seat_id in needs.seat_list()["playing"]:
			seat = needs.legacy_seats()[seat_id]
			if (seat.country or home) == (country or home) and seat.holds_household:
				with needs.legacy_act_as(seat_id):
					payers.append((self.visible_scale_of(needs.legacy_household_actor()), max(0.0, needs.revenue_estimate())))  # type: ignore[attr-defined]
		return payers

	def firm_taxpayers(self, country: Optional[str]) -> List[Tuple[float, float]]:
		"""(visible scale, taxable income) of the firms with a plant earning in `country`; the income is the part of the firm's
		that its plants on the country's tiles took (a firm with no plant placed elsewhere earns in the country it answers to)."""
		actors = self.registry
		home = actors.state.home_country
		return [(self.visible_scale_of(firm), income)  # type: ignore[attr-defined]
				for firm, income in taxpayer_income.firm_incomes_in(actors.active_firms(), country or home, actors.country_of,
																	actors.country_of_tile)]

	def visible_taxpayers(self) -> List[Tuple[float, float]]:
		"""(visible scale, taxable income) of every actor the home state can see: the home country's playing seats and the firms that answer to it."""
		needs = self.needs
		home = self.registry.state.home_country
		payers = self.seat_taxpayers(home)
		if not needs.seat_list()["playing"]:
			with needs.legacy_act_as(needs.acting_seat()):
				payers.append((self.visible_scale_of(needs.legacy_household_actor()), max(0.0, needs.revenue_estimate())))  # type: ignore[attr-defined]
		return payers + self.firm_taxpayers(home)
