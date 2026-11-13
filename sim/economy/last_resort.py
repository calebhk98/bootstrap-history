"""Lender of last resort: an actor (a state or a bank of issue) lends to a solvent bank facing a run, against collateral, at a penalty rate.

A bank that is solvent (its capital is not negative) but short of cash for the withdrawals asked of it borrows
the shortfall for a year instead of selling its loans at the secondary price. The penalty rate is the market rate plus
the bank's default risk, the share of its deposits its loss record puts beyond its capital (bank_runs.expected_loss_share),
so a sound bank pays little over the market and a shaky one pays dearly. The collateral is the bank's loans as their
lenders value them; the lender lends no more than the collateral covers with a year's interest, so it is repaid in full
if the collateral holds. An actor that issues money (a bank of issue) lends from nothing; any other lends from its purse.
A bank that is insolvent is refused: lending to it would only postpone the loss onto the lender.
"""
from typing import NamedTuple, Optional

from sim.refusal import Refusal

from . import credit_claims
from .types import EDGE_MINT, AgentId, Loan, Transfer

EPSILON = 1e-9
TERM_YEARS = 1.0
LENDING_PURPOSE = "last resort loan"


class Advance(NamedTuple):
    loan: Optional[Loan]
    refusal: Optional[Refusal]


def penalty_rate(market_rate: float, default_risk: float) -> float:
    """The market rate plus the bank's default risk."""
    return market_rate + max(0.0, default_risk)


def lendable(collateral_value: float, rate: float, wanted: float) -> float:
    """What the lender advances against the collateral: the amount wanted, at most what the collateral covers with a
    year's interest on it."""
    return max(0.0, min(wanted, collateral_value / (1.0 + rate * TERM_YEARS)))


def lend(record, lender: AgentId, issues_money: bool, bank_id: AgentId, wanted: float, market_rate: float,
         default_risk: float, year: int, money: str) -> Advance:
    """The lender advances `wanted` to the bank, or what its collateral and the lender's purse allow. The loan is
    struck in the shared registry with the bank as borrower, so the one rule services and defaults it."""
    bank_loans = [loan for loan in record.credit.loans.select(lender=bank_id)
                  if loan.borrower not in record.capital_markets.banks]
    collateral = credit_claims.claims_by_lender(bank_loans, money).get(bank_id, 0.0)
    owed = sum(deposit.principal + deposit.arrears for deposit in record.credit.loans.select(borrower=bank_id))
    held = record.book.balance(bank_id, money) + collateral + record.credit.contracts.deposit_value(bank_id)
    if held < owed:
        return Advance(None, Refusal("bank_insolvent", "%s holds less than it owes and is not lent to" % bank_id,
                                     assets=held, owed=owed))
    rate = penalty_rate(market_rate, default_risk)
    amount = lendable(collateral, rate, wanted)
    if not issues_money:
        amount = min(amount, max(0.0, record.book.balance(lender, money)))
    if amount <= EPSILON:
        return Advance(None, Refusal("no_collateral_or_funds", "%s cannot be lent against what it holds" % bank_id,
                                     collateral=collateral, wanted=wanted))
    loan = Loan("lastresort:%d:%s" % (year, bank_id), lender, bank_id, money, amount, rate=rate, years_left=TERM_YEARS,
                issued_year=year, collateral_value=collateral)
    record.book.transfer(Transfer(EDGE_MINT if issues_money else lender, bank_id, money, amount, LENDING_PURPOSE))
    return Advance(record.credit.add_loan(loan), None)
