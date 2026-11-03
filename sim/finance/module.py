"""The finance module: credit, debt, interest, arrears, insolvency, bondage and the capital market.

A household borrows against its standing earning and its name; past its limit nobody lends, projects halt, and in the end the
lenders write most of the debt off or put the debtor into service. The module owns each seat's debt state (`FinanceSeat`), answers
every question about the credit line, the rate, what can be spent and what debt the income can carry, applies the money phase's
debt steps, and runs the lenders' year. What it needs of other owners it reads as views and asks as commands; the agent economy's
rate and room come through bridge views until their owner moves."""
from sim.assembly.api import Module

from .applied import Applied
from .arrears import Arrears
from .bank import Bank
from .capital_market import CapitalMarket
from .cash_remedies import CashRemedies
from .credit_line import CreditLine
from .debt_service import DebtService
from .insolvency import Insolvency
from .purchases import Purchases


class Finance(Module):

	PARTS = {
		"applied": Applied,
		"capital_market": CapitalMarket,
		"credit_line": CreditLine,
		"arrears": Arrears,
		"insolvency": Insolvency,
		"debt_service": DebtService,
		"purchases": Purchases,
		"cash_remedies": CashRemedies,
		"bank": Bank,
	}
