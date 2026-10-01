"""What a state asks the simulated world when it budgets: its people, its prices, its taxpayers."""
from typing import Any, List, Tuple


class BudgetView:
	"""Read-only questions behind a state's standing need; mixed into `SimWorld`."""

	_sim: Any

	def population_total(self) -> float:
		return self._sim.population.total

	def state_capacity(self) -> float:
		return self._sim.state_capacity

	def army_headcount(self) -> float:
		"""Soldiers the state keeps: the opening force's share of the people, held as they change."""
		civ = self._sim.civ
		opening = float(civ.get("standing_army", 0.0))
		if opening <= 0.0:
			return 0.0
		return opening / float(civ["population"]) * self.population_total()

	def equipment_kg_per_soldier(self) -> float:
		"""Iron and ammunition one equipped soldier uses a year, at the equipment the state's
		armies have taken up from the founder's work."""
		sim = self._sim
		return sim.military_equipment_burden_kg_per_soldier_per_year(sim.state_military_diffusion())

	def pay_per_person_year(self, trade: str) -> float:
		return self._sim.HOURS_PER_PERSON_YEAR * self._sim.wage_per_hour(trade)

	def commodity_of(self, material: str) -> str:
		return self._sim._material_tag(material)[0]

	def material_cost(self, material: str, tonnes: float) -> float:
		"""Money to buy this many tonnes of a material at the price the market quotes."""
		quote = self._sim.material_purchase_cost(material, tonnes)
		return 0.0 if quote is None else quote[0]

	def local_labour_share(self) -> float:
		"""The share of the nation's labour that the founder's own labour market holds."""
		sim = self._sim
		return min(1.0, sim.home_town_population_estimate() / max(1.0, sim.population.total))

	def notice_over(self, scale: float) -> float:
		return self._sim.notice_over(scale)

	def visible_taxpayers(self) -> List[Tuple[float, float]]:
		"""(visible scale, taxable income) of every actor the state can see: the founder and the firms."""
		sim = self._sim
		payers = [(self.visible_scale_of(sim.household), max(0.0, sim.revenue()))]  # type: ignore[attr-defined]
		for firm in sim.actors.active_firms():
			payers.append((self.visible_scale_of(firm), max(0.0, firm.record.last_margin)))  # type: ignore[attr-defined]
		return payers
