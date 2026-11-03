"""A state's choice of how to meet a shortfall, and the parts of it that reach the books (fiscal_response.py)."""
from typing import Any, Dict, List

from sim.refusal import Refusal

from . import arrears, budget, fiscal_response, government_levers
from .budget_line import Line
from .liability import COLLECTIVE
from .tuning_fiscal import KIND_DEMAND_RATE_STEP, RATE_RAISE_STEP


class Fiscal:
	"""A state's response to a shortfall, on the government that owns the record and the purse."""

	def __init__(self, government: Any) -> None:
		self.government = government

	def meet_shortfall(self, lines: List[Line], world: Any) -> float:
		"""Choose, through the state's policy, how to cover what the lines need beyond the purse, and record the
		choice. The share of the need that is paid: all of it but what is neither borrowed nor covered from the purse."""
		need = sum(line.money for line in lines)
		gap = max(0.0, need - max(0.0, self.government.money))
		choice = fiscal_response.respond(self.government, world, lines, gap)
		self.government.record.fiscal_response = choice
		kind = choice.get(fiscal_response.KIND, 0.0)
		raised = choice.get(fiscal_response.RATE, 0.0)
		self.government.coinage.decide_debasement(world, choice.get(fiscal_response.DEBASE, 0.0))
		if kind > 0.0:
			self.demand_in_kind(kind, world)
		if raised > 0.0:
			self.raise_coin_rates(raised, world)
		self.pull_tax_response_levers(choice, world)
		return budget.share_paid(need, self.government.money, choice.get(fiscal_response.BORROW, 0.0))

	def pull_tax_response_levers(self, choice: Dict[str, float], world: Any) -> Dict[str, Any]:
		"""Set the tax-response levers the choice covered money with (the same levers a player pulls): collective liability, a
		full amnesty, and a remission of a step of the rate in the share of its yield the choice took. The levers it set."""
		context = government_levers.LeverContext(declared_forms=world.revenue.revenue_forms())
		wanted = {}
		if choice.get(fiscal_response.LIABILITY, 0.0) > 0.0:
			wanted[fiscal_response.LIABILITY] = COLLECTIVE
		if choice.get(fiscal_response.AMNESTY, 0.0) > 0.0:
			wanted[fiscal_response.AMNESTY] = 1.0
		capacity = fiscal_response.rate_cut_yield(world) if choice.get(fiscal_response.REMISSION, 0.0) > 0.0 else 0.0
		if capacity > 0.0:
			wanted[fiscal_response.REMISSION] = RATE_RAISE_STEP * min(1.0, choice[fiscal_response.REMISSION] / capacity)
		set_levers = {}
		for lever, value in wanted.items():
			change = government_levers.set_lever(self.government.record, {"lever": lever, "value": value}, context)
			if not isinstance(change, Refusal):
				set_levers[lever] = value
		return set_levers

	def deferred_fraction(self, lines: List[Line], share: float) -> float:
		"""Share of the pay left unpaid that the state's choice defers as owed (the rest is cut and never owed)."""
		choice = self.government.record.fiscal_response
		owing = sum(choice.get(name, 0.0) for name in (fiscal_response.ARREARS, fiscal_response.DEBASE,
														fiscal_response.LEVY, fiscal_response.KIND, fiscal_response.RATE,
														fiscal_response.LIABILITY, fiscal_response.AMNESTY, fiscal_response.REMISSION))
		pay_unpaid = sum(line.money * (1.0 - share) for line in lines if line.name in arrears.PAY_LINES)
		return min(1.0, owing / pay_unpaid) if pay_unpaid > 0.0 else 0.0

	def demand_in_kind(self, amount: float, world: Any) -> Dict[str, float]:
		"""Raise the rate of each form paid in kind, as far as `amount` of money's worth of the base reaches, through
		the same lever a player pulls; the rates it set. Next year's assessment is on them."""
		record = self.government.record
		forms = [form for form in world.revenue.revenue_forms() if form.get("paid_in") and form["rate"] > 0.0]
		capacity = fiscal_response.in_kind_base(record, world) * KIND_DEMAND_RATE_STEP
		if capacity <= 0.0:
			return {}
		fraction = min(1.0, amount / capacity)
		context = government_levers.LeverContext(declared_forms=world.revenue.revenue_forms())
		rates: Dict[str, float] = {}
		for form in forms:
			rate = min(1.0, form["rate"] * (1.0 + KIND_DEMAND_RATE_STEP * fraction))
			change = government_levers.set_lever(record, {"lever": government_levers.REVENUE, "name": form["form"],
														 "value": rate}, context)
			if not isinstance(change, Refusal):
				rates[form["form"]] = rate
		return rates

	def raise_coin_rates(self, amount: float, world: Any) -> Dict[str, float]:
		"""Raise the rate of each form collected in coin, as far as `amount` of money's worth of the base reaches,
		through the same lever a player pulls; the rates it set. Next year's assessment is on them."""
		raisable = fiscal_response.raisable_coin_forms(world)
		capacity = fiscal_response.rate_raise_yield(world)
		if capacity <= 0.0:
			return {}
		fraction = min(1.0, amount / capacity)
		context = government_levers.LeverContext(declared_forms=world.revenue.revenue_forms())
		rates: Dict[str, float] = {}
		for assessed in raisable:
			rate = min(1.0, assessed.rate * (1.0 + RATE_RAISE_STEP * fraction))
			change = government_levers.set_lever(self.government.record, {"lever": government_levers.REVENUE, "name": assessed.form,
																 "value": rate}, context)
			if not isinstance(change, Refusal):
				rates[assessed.form] = rate
		return rates

	def levy_sought(self) -> Dict[str, float]:
		"""The unfunded need the state chose to raise from the taxpayers it can see, by line."""
		unfunded = self.government.record.unfunded
		total = sum(unfunded.values())
		asked = self.government.record.fiscal_response.get(fiscal_response.LEVY, 0.0)
		if total <= 0.0 or asked <= 0.0:
			return {}
		share = min(1.0, asked / total)
		return {name: amount * share for name, amount in unfunded.items()}
