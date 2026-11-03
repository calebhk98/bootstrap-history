"""What an actor can see of the loanable-funds market of its civilisation, and what households save."""
from typing import Any, Optional, Tuple

from sim.agents.api import SAVING_SHARE_OF_SURPLUS
from sim.book import InsufficientFunds
from sim.economy.api import opening_market_rate
from sim.finance.api import DefaultOnDebt
from sim.world import demand

class Credit:
	"""Read-only questions about the market and about saving. `world` is the root that hands out the parts."""

	def __init__(self, world: Any) -> None:
		self.world = world

	@property
	def needs(self) -> Any:
		return self.world.needs

	def debt_service_share_of_surplus(self) -> float:
		return self.needs.debt_service_share_of_surplus()

	def market_rate(self) -> float:
		return self.needs.market_rate()

	def starting_rate(self) -> float:
		return opening_market_rate()

	def credit_headroom(self, actor_id: str) -> Optional[float]:
		"""What lenders will still advance an actor beyond what others owe; None before the market has met."""
		return self.needs.credit_room(actor_id)

	def fundable_amount(self, amount: float, existing_debt: float, collateral_value: float, arrears: float) -> Optional[float]:
		"""The most of a draw of `amount` the credit market lends an actor that owes `existing_debt` against `collateral_value`
		(the economy's one rule for every borrower); None before the market has met."""
		return self.needs.fundable_amount(amount, existing_debt, collateral_value, arrears)

	def risk_premium(self, debt_after: float, collateral_value: float, arrears: float) -> Optional[float]:
		"""The rate the credit market adds to the market rate for that debt against that collateral; None while the economy opens."""
		return self.needs.risk_premium(debt_after, collateral_value, arrears)

	def limit(self, actor_id: str, amount: float) -> float:
		"""The most of a draw of `amount` the account may be lent by the economy's rule: its actor's own (`rule_limit`), a seat
		household's by its credit line less its debt, the whole of it for an account nobody stands behind (an edge, the pool): the
		lenders' supply bounds the draw either way (`Purses.drawable`)."""
		actor = self.world.registry.actors.get(actor_id)
		if actor is not None:
			return actor.rule_limit(self.world, amount)
		if actor_id in self.needs.seat_list()["households"]:
			with self.needs.act_as(actor_id):
				debt = max(0.0, -self.needs.acting_balance())
				return max(0.0, min(amount, self.needs.credit_limit() - debt))
		return amount

	def rate_ceiling(self, account: str, amount: float) -> float:
		"""The yearly rate the account would pay on a draw of `amount`, which no lender asking more may be asked to lend: its actor's
		or its seat household's own rate on the debt then owed, else the market rate (the least any borrower pays, and what the pool
		earns on what it lends)."""
		actor = self.world.registry.actors.get(account)
		if actor is not None:
			return actor.rate_on_loan(self.world, amount)
		if account in self.needs.seat_list()["households"]:
			with self.needs.act_as(account):
				return self.needs.household_rate_on_loan(amount)
		return self.market_rate()

	def state_may_borrow(self, state: Any) -> bool:
		"""Whether a state holds a technology that declares the `state_credit` mechanic, in its own
		knowledge or in what its society already knows."""
		return any(state.knows(node_id, self.world) for node_id in self.nodes_with_mechanic("state_credit"))

	def nodes_with_mechanic(self, mechanic: str) -> Any:
		"""The tree nodes that declare a mechanic."""
		return tuple(self.needs.mechanic[mechanic])

	def state_lending(self) -> Tuple[float, float]:
		"""(what the state has out on loan, the yearly rate lenders earn) at the last meeting."""
		return self.needs.state_lending()

	def pay_interest(self, payer: Any, owed: float, purpose: str = "interest") -> float:
		"""A borrower pays the interest on its debt to its lenders; what was paid. Interest the lenders refuse to advance the
		payer (its limit, or the funds they hold) is not paid: the caller carries it as arrears."""
		try:
			received = payer.purses.pay_interest(payer.account_id, owed)
		except InsufficientFunds:
			return 0.0
		paid = sum(received.values())
		payer.payments.note_outlay(purpose, paid)
		return paid

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
		income = self.world.revenue.society_output()
		if population <= 0.0 or income <= 0.0:
			return 0.0
		labour = self.world.labour
		need_per_person = labour.pay_per_person_year(labour.trade_of_role("unskilled")) * self.needs.working_age() / population
		bins = demand.income_bins(population, income / population)
		surplus = sum(income_bin.population * max(0.0, income_bin.income_per_capita_per_year - need_per_person)
					  for income_bin in bins)
		return SAVING_SHARE_OF_SURPLUS * surplus
