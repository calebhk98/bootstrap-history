"""The purchase budget and its refusal, as the views every buyer reads.

Needs: money_text, acting_balance (and what `cash_remedies` reads)."""
from typing import Any

from . import purchase_rules
from .constants import SPENDING_DRAW_SHARE_ORDINARY


class Purchases:

	def purchase_budget(self) -> float:
		"""Most the acting seat can spend on one outright purchase right now."""
		return self.spending_power(purchase_rules.BUDGET_KIND)

	def can_pay(self, cost: float) -> bool:
		"""Whether the acting seat's purchase budget covers `cost`."""
		return purchase_rules.can_pay(cost, self.purchase_budget())

	def affordable_units(self, unit_cost: float, decimals: int = 1) -> float:
		"""Units the purchase budget buys at `unit_cost`, rounded down so the figure is buyable."""
		return purchase_rules.affordable_units(self.purchase_budget(), unit_cost, decimals)

	def afford_means(self) -> str:
		return purchase_rules.afford_means()

	def purchase_remedies_text(self) -> str:
		"""The commands that raise cash or cut costs, or an empty string."""
		return purchase_rules.remedies_sentence(self.cash_remedies())

	def purchase_refusal(self, what: str, cost: float) -> Any:
		"""The refusal that states the purchase rule, the budget and the amount short."""
		needs = self.needs
		budget = self.purchase_budget()
		short = max(0.0, cost - budget)
		return purchase_rules.cash_short(
			what, cost, budget, SPENDING_DRAW_SHARE_ORDINARY, needs.money_text(needs.acting_balance(), grouped=True),
			needs.money_text(cost, grouped=True), needs.money_text(budget, grouped=True), needs.money_text(short, grouped=True),
			needs.money_text(self.credit_limit(), grouped=True), self.purchase_remedies_text())
