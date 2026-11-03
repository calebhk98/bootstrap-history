"""What actors ask of the home labour market: what a trade pays, who is free to hire, how many practise it."""
from typing import Any, Optional

from sim.agents.api import payroll
from sim.labour import api as labour_api


class ActorLabourReads:
	"""The one labour market every employer asks, and the people of each trade. `world` is the root that hands out the parts."""

	def __init__(self, world: Any) -> None:
		self.world = world

	@property
	def needs(self) -> Any:
		return self.world.needs

	@property
	def labour_market(self) -> Any:
		"""The one labour market every employer asks: quote, hire, release, read the pressure."""
		return self.needs.labour_market()

	@property
	def hours_per_person_year(self) -> float:
		return self.needs.hours_per_person_year()

	def pay_per_person_year(self, trade: str) -> float:
		return self.labour_market.quote_annual(trade)

	def hourly_pay(self, trade: str) -> Optional[float]:
		"""What an hour of a trade pays at the going wage of the home labour market."""
		return float(self.labour_market.quote(trade))

	def pay_wages(self, payer: Any, amount: float, purpose: Any) -> None:
		"""Wages the home country's people are paid: they reach the strata's purses."""
		payroll.pay_wages(self.world.registry, payer, amount, purpose, self.world)

	def national_people(self, trade: str) -> float:
		"""People of a trade in the whole country; the working age for unskilled labour."""
		return self.needs.working_age() if trade == self.trade_of_role("unskilled") else self.needs.trade_population[trade]

	def trade_exists(self, trade: str) -> bool:
		return self.needs.trade_available[trade]

	def trade_of_role(self, role: str) -> str:
		return labour_api.trade_of_role(self.needs.trade_registry(), role)

	def free_fte(self, trade: str, actor_id: Optional[str]) -> Optional[float]:
		"""People of a trade left in the pool for this actor after the founder's staff and
		everyone else's. A trade nobody here practises has the people the founder taught as its pool;
		None for a trade that cannot be had at all."""
		needs = self.needs
		if not needs.trade_available[trade]:
			return None
		exist = needs.taught_trade_people[trade] if trade in needs.trades_absent() else needs.people_who_exist[trade]
		founder = needs.staff_on_all_books[trade]
		return max(0.0, exist - founder - self.world.registry.staff.home_staff_fte(trade, excluding=actor_id))
