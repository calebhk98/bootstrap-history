"""The capital markets' part of the economy's year, called from `Economy._run_year` so that file holds one line each.

Before the year's lending the holders of shares and loans may sell (secondary_trade.py), the households short of
cash among them selling for the cash they would otherwise borrow; then depositors review their banks, and a bank
asked for more than it holds sells loans or fails (bank_runs.py).
"""
from typing import Dict, List, Sequence

from . import bank_runs, lending, secondary_trade
from .secondary_trade import Shortfall
from .types import AgentId, FundsOffer


def holds_a_claim(record) -> bool:
    """Whether any household holds shares or a loan it could sell."""
    if any(holders for holders in record.shares.values()):
        return True
    return any(loan.lender in record.cohorts and secondary_trade.tradable(record, loan) for loan in record.loans)


def shortfalls(setup, record, view, ledger) -> Dict[AgentId, Shortfall]:
    """What each household short of cash for its floors would borrow, and the most it would pay to."""
    requests = lending.household_requests(setup, record, view, ledger, {})
    return {request.borrower: Shortfall(request.amount, request.maximum_rate)
            for request in requests if request.borrower in record.cohorts}


def trade(setup, record, view, ledger, funds: Sequence[FundsOffer], institutions: Sequence[str]) -> List[FundsOffer]:
    """The year's secondary trading; the offers with what buyers spent taken off."""
    if not any(name in institutions for name in (secondary_trade.SHARE_TRADING, secondary_trade.BOND_MARKET)):
        return list(funds)
    if not holds_a_claim(record):
        return list(funds)
    remaining, _trades = secondary_trade.run(setup, record, funds, shortfalls(setup, record, view, ledger),
                                             view.interest_rate(setup.currency_id), institutions)
    return remaining


def before_lending(setup, record, view, ledger, funds: Sequence[FundsOffer], year: int,
                   institutions: Sequence[str]) -> List[FundsOffer]:
    """The offers savers bring to the year's lending, after secondary trading and the withdrawals from banks."""
    funds = trade(setup, record, view, ledger, funds, institutions)
    if not record.banks:
        return funds
    return bank_runs.run(setup, record, funds, year, institutions, view.interest_rate(setup.currency_id))
