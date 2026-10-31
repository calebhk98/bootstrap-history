"""What an actor can see of the loanable-funds market of its civilisation, and what households save."""
from typing import Any, Optional, Tuple

from sim.agents.api import SAVING_SHARE_OF_SURPLUS
from sim.economy.api import opening_market_rate
from sim.finance.api import DefaultOnDebt
from sim.world import demand

class CapitalView:
	"""Read-only questions about the market and about saving; mixed into `ActorWorld`."""

	needs: Any

	def debt_service_share_of_surplus(self) -> float:
		return self.needs.debt_service_share_of_surplus()

	def market_rate(self) -> float:
		return self.needs.market_rate()

	def starting_rate(self) -> float:
		return opening_market_rate()

	def credit_headroom(self, actor_id: str) -> Optional[float]:
		"""What lenders will still advance an actor beyond what others owe; None before the market has met."""
		return self.needs.credit_room(actor_id)

	def state_may_borrow(self, state: Any) -> bool:
		"""Whether a state holds a technology that declares the `state_credit` mechanic, in its own
		knowledge or in what its society already knows."""
		return any(state.knows(node_id, self) for node_id in self.nodes_with_mechanic("state_credit"))

	def nodes_with_mechanic(self, mechanic: str) -> Any:
		"""The tree nodes that declare a mechanic."""
		return tuple(self.needs.mechanic[mechanic])

	def state_lending(self) -> Tuple[float, float]:
		"""(what the state has out on loan, the yearly rate lenders earn) at the last meeting."""
		return self.needs.state_lending()

	def pay_interest(self, payer: Any, owed: float, purpose: str = "interest") -> None:
		"""A borrower pays the interest on its debt to its lenders."""
		received = payer.purses.pay_interest(payer.account_id, owed)
		payer.note_outlay(purpose, sum(received.values()))

	def founder_credit_limit(self) -> float:
		"""The most the founder's household may owe in all."""
		return self.needs.credit_limit()

	def founder_debt_rate(self) -> float:
		return self.needs.debt_interest_rate()

	def founder_defaults(self) -> None:
		self.needs.send(DefaultOnDebt(self.needs.year()))

	def household_saving(self) -> float:
		"""Yearly saving of the society's households: a share of the income above subsistence, with
		income spread over the people as the civilisation's inequality says. A labourer's yearly pay keeps
		him and his dependents at the wage floor, so it is what each person needs, spread over everyone."""
		population = self.needs.population_total()
		income = self.society_output()  # type: ignore[attr-defined]
		if population <= 0.0 or income <= 0.0:
			return 0.0
		need_per_person = self.pay_per_person_year("labourer") * self.needs.working_age() / population  # type: ignore[attr-defined]
		bins = demand.income_bins(population, income / population)
		surplus = sum(income_bin.population * max(0.0, income_bin.income_per_capita_per_year - need_per_person)
					  for income_bin in bins)
		return SAVING_SHARE_OF_SURPLUS * surplus
