"""The finance module's debt state view, its command handlers and the credit-limit phase."""
from typing import Any, Dict

from sim.assembly.api import Part


class Applied(Part):

	def debt_status(self) -> Dict[str, Any]:
		"""The acting seat's debt: the year nobody funds new work before, its insolvent years, its arrears, its bondage term and
		debt, the interest it has paid and the year of its last settlement."""
		seat = self.seat
		return {"credit_frozen_until": seat.credit_frozen_until, "insolvent_years": seat.insolvent_years,
		        "interest_arrears": seat.interest_arrears, "arrears_years": seat.arrears_years,
		        "bondage_years_left": seat.bondage_years_left, "bondage_debt": seat.bondage_debt,
		        "last_settlement": seat.last_settlement, "interest_paid": seat.interest_paid}

	def apply_default_on_debt(self, command: Any) -> None:
		self.parts.insolvency.default_on_debt(command.year)

	def apply_charge_interest(self, command: Any) -> float:
		return self.parts.arrears.charge_interest(command.year)

	def apply_shed_loss_makers(self, command: Any) -> None:
		self.parts.arrears.shed_loss_makers(command.year)

	def apply_warn_near_limit(self, command: Any) -> None:
		self.parts.arrears.warn_near_the_limit(command.year)

	def apply_enforce_credit_limit(self, command: Any) -> None:
		self.parts.insolvency.enforce_credit_limit(command.year)

	def step_credit_limit(self, seat_id: str) -> None:
		"""The `credit_limit` phase: past the limit the seat simply stops."""
		self.parts.insolvency.enforce_credit_limit(self.needs.year())
