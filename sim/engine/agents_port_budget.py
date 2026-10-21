"""What a state asks the simulated world when it budgets: its people, its prices, its taxpayers."""
from typing import Any, List, Optional, Tuple

from sim.agents.api import DOLE_MATERIAL, THREAT_ARMY_RESPONSE, Hands
from sim.world import agriculture, demand
from sim.geography.api import territory, tiles_held


class BudgetView:
	"""Read-only questions behind a state's standing need; mixed into `SimWorld`."""

	_sim: Any

	def population_total(self) -> float:
		return self._sim.population.total

	def state_reach(self) -> float:
		return self._sim.state_authority()

	def territory(self) -> Any:
		"""Frontier, coast and road length of the tiles the state holds."""
		return territory.holdings(tiles_held(self._sim.civ))

	def country_strata(self) -> List[Any]:
		"""The bodies of people (strata actors) of the state's own country, in id order."""
		return [stratum for stratum in self._sim.actors.of_kind("stratum") if stratum.record.country is None]

	def literacy(self, field: str) -> float:
		return self._sim.literacy(field)

	def research_productivity(self, country=None) -> float:
		return self._sim.research_productivity(country)

	def urban_population(self) -> float:
		return self.population_total() * float(self._sim.civ.get("urban_fraction", 0.0))

	def subsistence_kg_per_person_year(self) -> float:
		return demand.FOOD_SUBSISTENCE_QUANTITY_KG_PER_CAPITA_PER_YEAR

	def national_people(self, trade: str) -> float:
		"""People of a trade in the whole country; the working age for unskilled labour."""
		sim = self._sim
		return sim.population.working_age if trade == "labourer" else sim.labour.national_trade_population(trade)

	def trade_exists(self, trade: str) -> bool:
		return self._sim.labour.trade_available(trade)

	def threat_pressure(self) -> float:
		"""Probability a year of the civilisation's own hazards sack a site: the declared
		sack chances of those running now, before any relief the founder has bought."""
		year = self.year
		return sum(float(hazard.get("sack_chance", 0.0)) for hazard in self._sim.civ.get("hazards", [])
				   if hazard.get("years") and hazard["years"][0] <= year <= hazard["years"][1])

	def army_wanted(self) -> float:
		"""Soldiers the state wants: the opening force the civilisation starts with, raised by the
		threat its hazards describe. The garrison follows the frontier, not the head count."""
		opening = float(self._sim.civ.get("standing_army", 0.0))
		return max(0.0, opening * (1.0 + THREAT_ARMY_RESPONSE * self.threat_pressure()))

	def soldiers_under_arms(self) -> float:
		"""Soldiers the state keeps now: what it paid for last year, else the force it wants."""
		kept = self.government().record.army
		return kept if kept > 0.0 else self.army_wanted()

	def state_hands(self) -> Any:
		"""The people and food the country can give its state: the working age, the farm hands the society's
		farming wants (none known before its first allocation), and the share of the people's food need the last
		year's supply met, with the state's own granary making up what the harvest lacked."""
		sim = self._sim
		hours = sim.state.holdings.farm_hours_needed
		farm_hands = 0.0 if hours is None else hours / agriculture.ANNUAL_LABOUR_HOURS_PER_FARM_WORKER
		flows = getattr(sim, "_last_demographic_step", None)
		ratio = 1.0 if flows is None else float(flows.nutrition_ratio)
		need_tonnes = sim.population.total * self.subsistence_kg_per_person_year() / 1000.0
		granary = self.government().record.stores.get(DOLE_MATERIAL, 0.0)
		return Hands(sim.population.working_age, farm_hands, min(1.0, ratio + (granary / need_tonnes if need_tonnes > 0.0 else 0.0)))

	def patron_ask(self) -> float:
		return self._sim.patron_funding_ask()

	def equipment_kg_per_soldier(self) -> float:
		"""Iron and ammunition one equipped soldier uses a year, at the equipment the state's
		armies have taken up from the founder's work."""
		sim = self._sim
		return sim.military_equipment_burden_kg_per_soldier_per_year(sim.state_military_diffusion())

	def military_work_ids(self) -> Tuple[str, ...]:
		return tuple(self._sim._diffusible_ids("military"))

	def equipment_kg_at_adoption(self, adoption: float) -> float:
		return self._sim.military_equipment_burden_kg_per_soldier_per_year(adoption)

	def pay_per_person_year(self, trade: str) -> float:
		return self.labour_market.quote_annual(trade)  # type: ignore[attr-defined]

	def commodity_of(self, material: str) -> str:
		return self._sim.economy.commodity_of(material)

	def material_cost(self, material: str, tonnes: float) -> Optional[float]:
		"""Money to buy this many tonnes of a material at the price the market quotes; None when nothing sells it."""
		quote = self._sim.economy.purchase_cost(material, tonnes)
		return None if quote is None else quote[0]

	def fleet_goods(self, holder_id: Optional[str] = None) -> List[Any]:
		"""Available naval vessels, their crews, service lives and a state's holdings (the founder's state's by default)."""
		return self._sim.economy.fleet_goods(holder_id or self.government().actor_id)

	def local_staff(self, trade: str, people: float) -> float:
		"""How many of `people` kept in a trade nationwide come out of the founder's own labour
		market: the share of the nation's people of that trade they are, applied to the pool the
		founder can reach. Unskilled labour is the whole working age."""
		sim = self._sim
		nation = sim.population.working_age if trade == "labourer" else sim.labour.national_trade_population(trade)
		if nation <= 0.0:
			return 0.0
		reach = sim.labour.reachable_trade_population(trade) + sim.actor_staff_fte(trade)
		return min(1.0, people / nation) * reach

	def notice_over(self, scale: float, capacity: Optional[float] = None) -> float:
		return self._sim.notice_over(scale, capacity)

	def seat_taxpayers(self, country: Optional[str]) -> List[Tuple[float, float]]:
		"""(visible scale, taxable income) of the playing household seats that belong to `country`; a seat with no
		country belongs to the game's own (home) country."""
		sim = self._sim
		home = sim.actors.state.home_country
		payers = []
		for seat_id in sim.playing_seats():
			seat = sim.state.seats[seat_id]
			if (seat.country or home) == (country or home) and seat.holds_household:
				with sim.act_as(seat_id):
					payers.append((self.visible_scale_of(sim.household), max(0.0, sim.revenue())))  # type: ignore[attr-defined]
		return payers

	def visible_taxpayers(self) -> List[Tuple[float, float]]:
		"""(visible scale, taxable income) of every actor the home state can see: the home country's playing seats and the firms."""
		sim = self._sim
		payers = self.seat_taxpayers(sim.actors.state.home_country)
		if not sim.playing_seats():
			with sim.act_as(sim.state.acting_seat):
				payers.append((self.visible_scale_of(sim.household), max(0.0, sim.revenue())))  # type: ignore[attr-defined]
		for firm in sim.actors.active_firms():
			payers.append((self.visible_scale_of(firm), max(0.0, firm.record.last_margin)))  # type: ignore[attr-defined]
		return payers
