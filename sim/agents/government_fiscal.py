"""A state's choice of how to meet a shortfall, and the parts of it that reach the books (fiscal_response.py)."""
from typing import Any, Dict, List

from . import arrears, fiscal_response, government_levers
from .government_coinage import debasement_decision
from .budget_line import Line
from .tuning_fiscal import KIND_DEMAND_RATE_STEP


class FiscalMixin:
	"""Mixed into `Government`."""

	def meet_shortfall(self, lines: List[Line], world: Any) -> float:
		"""Choose, through the state's policy, how to cover what the lines need beyond the purse, and record the
		choice. The share of the need that is paid: all of it but what is neither borrowed nor covered from the purse."""
		need = sum(line.money for line in lines)
		gap = max(0.0, need - max(0.0, self.money))  # type: ignore[attr-defined]
		choice = fiscal_response.respond(self, world, lines, gap)
		self.record.fiscal_response = choice  # type: ignore[attr-defined]
		unpaid = gap - choice.get(fiscal_response.BORROW, 0.0)
		kind = choice.get(fiscal_response.KIND, 0.0)
		self.apply_debasement(choice.get(fiscal_response.DEBASE, 0.0), world)
		if kind > 0.0:
			self.demand_in_kind(kind, world)
		return 1.0 if need <= 0.0 else max(0.0, 1.0 - unpaid / need)

	def apply_debasement(self, amount: float, world: Any) -> float:
		"""Cut the metal in the coin as far as covering `amount` of the shortfall takes; the cut, recorded."""
		share = debasement_decision(self, world, amount)
		self.record.coin_cut_share = share  # type: ignore[attr-defined]
		self.record.coin_metal_kept *= 1.0 - share  # type: ignore[attr-defined]
		return share

	def deferred_fraction(self, lines: List[Line], share: float) -> float:
		"""Share of the pay left unpaid that the state's choice defers as owed (the rest is cut and never owed)."""
		choice = self.record.fiscal_response  # type: ignore[attr-defined]
		owing = sum(choice.get(name, 0.0) for name in (fiscal_response.ARREARS, fiscal_response.DEBASE,
														fiscal_response.LEVY, fiscal_response.KIND))
		pay_unpaid = sum(line.money * (1.0 - share) for line in lines if line.name in arrears.PAY_LINES)
		return min(1.0, owing / pay_unpaid) if pay_unpaid > 0.0 else 0.0

	def demand_in_kind(self, amount: float, world: Any) -> Dict[str, float]:
		"""Raise the rate of each form paid in kind, as far as `amount` of money's worth of the base reaches, through
		the same lever a player pulls; the rates it set. Next year's assessment is on them."""
		record = self.record  # type: ignore[attr-defined]
		forms = [form for form in world.revenue_forms() if form.get("paid_in") and form["rate"] > 0.0]
		capacity = fiscal_response.in_kind_base(record, world) * KIND_DEMAND_RATE_STEP
		if capacity <= 0.0:
			return {}
		fraction = min(1.0, amount / capacity)
		context = government_levers.LeverContext(declared_forms=world.revenue_forms())
		rates: Dict[str, float] = {}
		for form in forms:
			rate = min(1.0, form["rate"] * (1.0 + KIND_DEMAND_RATE_STEP * fraction))
			change = government_levers.set_lever(record, {"lever": government_levers.REVENUE, "name": form["form"],
														 "value": rate}, context)
			if not hasattr(change, "cause"):
				rates[form["form"]] = rate
		return rates

	def levy_sought(self) -> Dict[str, float]:
		"""The unfunded need the state chose to raise from the taxpayers it can see, by line."""
		unfunded = self.record.unfunded  # type: ignore[attr-defined]
		total = sum(unfunded.values())
		asked = self.record.fiscal_response.get(fiscal_response.LEVY, 0.0)  # type: ignore[attr-defined]
		if total <= 0.0 or asked <= 0.0:
			return {}
		share = min(1.0, asked / total)
		return {name: amount * share for name, amount in unfunded.items()}
