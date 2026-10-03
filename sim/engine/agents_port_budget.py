"""What a state asks the simulated world when it budgets: its people, its prices, its taxpayers."""
from typing import Any, List, Tuple

from sim.agents.api import THREAT_ARMY_RESPONSE
from sim.world import demand
from sim.geography.api import territory


class BudgetView:
	"""Read-only questions behind a state's standing need; mixed into `SimWorld`."""

	_sim: Any

	def population_total(self) -> float:
		return self._sim.population.total

	def state_capacity(self) -> float:
		return self._sim.state_capacity

	def territory(self) -> Any:
		"""Frontier, coast and road length of the tiles the state holds."""
		return territory.holdings(list(self._sim.civ.get("home_regions") or []))

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

	def patron_ask(self) -> float:
		return self._sim.patron_funding_ask()

	def equipment_kg_per_soldier(self) -> float:
		"""Iron and ammunition one equipped soldier uses a year, at the equipment the state's
		armies have taken up from the founder's work."""
		sim = self._sim
		return sim.military_equipment_burden_kg_per_soldier_per_year(sim.state_military_diffusion())

	def pay_per_person_year(self, trade: str) -> float:
		return self.labour_market.quote_annual(trade)  # type: ignore[attr-defined]

	def commodity_of(self, material: str) -> str:
		return self._sim.economy.commodity_of(material)

	def material_cost(self, material: str, tonnes: float) -> float:
		"""Money to buy this many tonnes of a material at the price the market quotes."""
		quote = self._sim.economy.purchase_cost(material, tonnes)
		return 0.0 if quote is None else quote[0]

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

	def notice_over(self, scale: float) -> float:
		return self._sim.notice_over(scale)

	def visible_taxpayers(self) -> List[Tuple[float, float]]:
		"""(visible scale, taxable income) of every actor the state can see: the founder and the firms."""
		sim = self._sim
		payers = [(self.visible_scale_of(sim.household), max(0.0, sim.revenue()))]  # type: ignore[attr-defined]
		for firm in sim.actors.active_firms():
			payers.append((self.visible_scale_of(firm), max(0.0, firm.record.last_margin)))  # type: ignore[attr-defined]
		return payers
