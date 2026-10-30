"""The finance module: credit, debt, interest, arrears, insolvency, bondage and the capital market.

A household borrows against its standing earning and its name; past its limit nobody lends, projects halt, and in the end the
lenders write most of the debt off or put the debtor into service. The module owns each seat's debt state (`FinanceSeat`), answers
every question about the credit line, the rate, what can be spent and what debt the income can carry, applies the money phase's
debt steps, and runs the lenders' year. What it needs of other owners it reads as views and asks as commands; the agent economy's
rate and room come through bridge views until their owner moves."""
from typing import Any, Dict

from sim.assembly.api import Module

from .arrears import Arrears
from .bank import Bank
from .capital_market import CapitalMarket
from .cash_remedies import CashRemedies
from .credit_line import CreditLine
from .debt_service import DebtService
from .insolvency import Insolvency
from .purchases import Purchases


class Finance(CapitalMarket, CreditLine, Arrears, Insolvency, DebtService, Purchases, CashRemedies, Bank, Module):

	# ---- the seat's debt state ----

	def debt_status(self) -> Dict[str, Any]:
		"""The acting seat's debt: the year nobody funds new work before, its insolvent years, its arrears, its bondage term and
		debt, the interest it has paid and the year of its last settlement."""
		seat = self.seat
		return {"credit_frozen_until": seat.credit_frozen_until, "insolvent_years": seat.insolvent_years,
		        "interest_arrears": seat.interest_arrears, "arrears_years": seat.arrears_years,
		        "bondage_years_left": seat.bondage_years_left, "bondage_debt": seat.bondage_debt,
		        "last_settlement": seat.last_settlement, "interest_paid": seat.interest_paid}

	# ---- the commands ----

	def apply_default_on_debt(self, command: Any) -> None:
		self.default_on_debt(command.year)

	def apply_charge_interest(self, command: Any) -> float:
		return self.charge_interest(command.year)

	def apply_shed_loss_makers(self, command: Any) -> None:
		self.shed_loss_makers(command.year)

	def apply_warn_near_limit(self, command: Any) -> None:
		self.warn_near_the_limit(command.year)

	def apply_enforce_credit_limit(self, command: Any) -> None:
		self.enforce_credit_limit(command.year)

	def step_credit_limit(self, seat_id: str) -> None:
		"""The `credit_limit` phase: past the limit the seat simply stops."""
		self.enforce_credit_limit(self.needs.year())
