"""What an actor can see of the loanable-funds market of its civilisation, and what households save."""
from typing import Any, Optional, Tuple

from sim.constants import declare
from sim.world import demand

SAVING_SHARE_OF_SURPLUS = declare(
	"SAVING_SHARE_OF_SURPLUS", 0.2, kind="temporary_heuristic",
	unit="share of income above subsistence", source=None, confidence="D",
	why="What households put aside rather than consume from the income they have above what keeps them "
		"fed. Stands in for a saving model with time preference, bequest and risk.")


class CapitalView:
	"""Read-only questions about the market and about saving; mixed into `SimWorld`."""

	_sim: Any

	def market_rate(self) -> float:
		return self._sim.economy.base_rate()

	def starting_rate(self) -> float:
		return float(self._sim.civ["starting_interest_rate"])

	def credit_headroom(self, actor_id: str) -> Optional[float]:
		"""What lenders will still advance an actor beyond what others owe; None before the market has met."""
		return self._sim.economy.credit_room(actor_id)

	def state_may_borrow(self, state: Any) -> bool:
		"""Whether a state holds a technology that declares the `state_credit` mechanic, in its own
		knowledge or in what its society already knows."""
		return any(state.knows(node_id, self) for node_id in self._sim.nodes_with_mechanic("state_credit"))

	def state_lending(self) -> Tuple[float, float]:
		"""(what the state has out on loan, the yearly rate lenders earn) at the last meeting."""
		return self._sim.state_lending()

	def note_interest_paid(self, amount: float) -> None:
		"""A borrower's interest joins the pool lenders are paid from."""
		self._sim.economy.report_interest_paid(amount)

	def household_saving(self) -> float:
		"""Yearly saving of the society's households: a share of the income above subsistence, with
		income spread over the people as the civilisation's inequality says. A labourer's yearly pay keeps
		him and his dependents at the wage floor, so it is what each person needs, spread over everyone."""
		sim = self._sim
		population = sim.population.total
		income = self.society_output()  # type: ignore[attr-defined]
		if population <= 0.0 or income <= 0.0:
			return 0.0
		need_per_person = self.pay_per_person_year("labourer") * sim.population.working_age / population  # type: ignore[attr-defined]
		bins = demand.income_bins(population, income / population)
		surplus = sum(income_bin.population * max(0.0, income_bin.income_per_capita_per_year - need_per_person)
					  for income_bin in bins)
		return SAVING_SHARE_OF_SURPLUS * surplus
