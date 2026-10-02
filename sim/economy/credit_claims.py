"""Loans as assets and liabilities: what a lender holds as claims, what a borrower owes, and what lenders remember.

A loan is a pair of entries, a claim for its lender and a debt for its borrower, kept on the record's loan
list rather than in the book (the book holds only what can be spent). Money moves only by transfers, so
conservation of money is untouched; wealth is the money in the book plus claims less debts. Summed over
every agent the claims and the debts are the same loans, so credit creates no net wealth, and a default
removes the claim and the debt together: the lender is poorer by what it expected to collect, the borrower
is freed of it, and no money moves.
"""
from typing import Dict, Iterable, Mapping, Sequence

from sim.constants import declare

from .credit import DEFAULT_ARREARS_SHARE, Default
from .types import AgentId, CurrencyId, Loan

DEFAULT_MEMORY_SHARE_PER_YEAR = declare(
    "DEFAULT_MEMORY_SHARE_PER_YEAR", 0.2, kind="temporary_heuristic",
    unit="share of a remembered default forgotten each year", source=None, confidence="D",
    why="Lenders price a borrower that once defaulted as risky for a while: its unpaid loss counts as "
        "arrears in the premium and fades. Stands in for credit reputation and bankruptcy law, which "
        "are not modelled.")


def claim_value(loan: Loan) -> float:
    """What the lender expects to collect: the principal, and the arrears less the share it doubts. Doubt
    rises with arrears until the write-off point, where the arrears are worth nothing."""
    if loan.principal <= 0.0:
        return max(0.0, loan.arrears)
    doubt = min(1.0, loan.arrears / (DEFAULT_ARREARS_SHARE * loan.principal))
    return loan.principal + loan.arrears * (1.0 - doubt)


def claims_by_lender(loans: Iterable[Loan], currency: CurrencyId = None) -> Dict[AgentId, float]:
    held: Dict[AgentId, float] = {}
    for loan in loans:
        if currency is None or loan.currency == currency:
            held[loan.lender] = held.get(loan.lender, 0.0) + claim_value(loan)
    return held


def debts_by_borrower(loans: Iterable[Loan], currency: CurrencyId = None) -> Dict[AgentId, float]:
    """What each borrower owes: principal and the arrears it has not paid."""
    owed: Dict[AgentId, float] = {}
    for loan in loans:
        if currency is None or loan.currency == currency:
            owed[loan.borrower] = owed.get(loan.borrower, 0.0) + loan.principal + loan.arrears
    return owed


def principal_by_borrower(loans: Iterable[Loan]) -> Dict[AgentId, float]:
    owed: Dict[AgentId, float] = {}
    for loan in loans:
        owed[loan.borrower] = owed.get(loan.borrower, 0.0) + loan.principal
    return owed


def wealth(book, loans: Sequence[Loan], agent: AgentId, currency: CurrencyId) -> float:
    """Money in the book plus claims less debts."""
    claims = claims_by_lender((loan for loan in loans if loan.lender == agent), currency).get(agent, 0.0)
    debts = debts_by_borrower((loan for loan in loans if loan.borrower == agent), currency).get(agent, 0.0)
    return book.balance(agent, currency) + claims - debts


def arrears_history(loans: Iterable[Loan], remembered_losses: Mapping[AgentId, float]) -> Dict[AgentId, float]:
    """What the market holds against each borrower: its arrears now plus the losses it caused earlier."""
    history = dict(remembered_losses)
    for loan in loans:
        history[loan.borrower] = history.get(loan.borrower, 0.0) + loan.arrears
    return history


def remember_defaults(remembered: Mapping[AgentId, float], defaults: Iterable[Default]) -> Dict[AgentId, float]:
    """Remembered losses fade by the declared share a year; this year's defaults join them."""
    kept = {agent: loss * (1.0 - DEFAULT_MEMORY_SHARE_PER_YEAR) for agent, loss in remembered.items()}
    for default in defaults:
        kept[default.borrower] = kept.get(default.borrower, 0.0) + default.loss
    return {agent: loss for agent, loss in sorted(kept.items()) if loss > 1e-9}


def losses_by_lender(defaults: Iterable[Default]) -> Dict[AgentId, float]:
    lost: Dict[AgentId, float] = {}
    for default in defaults:
        lost[default.lender] = lost.get(default.lender, 0.0) + default.loss
    return lost
