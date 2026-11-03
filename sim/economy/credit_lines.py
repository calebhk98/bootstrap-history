"""Credit lines in the clearing (Complaint 665). An actor whose money the engine keeps (the founder, any other
seat) asks the credit market for its line like every other borrower: its request joins `credit.clear`, ordered by
its ceiling, and what the clearing grants it is its room. No money moves in the economy's book for it, since its
purse is the engine's. The reserve lenders keep back is held out of every lender's offer alike.
"""
from dataclasses import dataclass, replace
from typing import Dict, Iterable, List, Sequence, Tuple

from sim.world import capital_market

from . import banks, credit, credit_cap
from .types import AgentId, CurrencyId, FundsOffer, Loan, LoanRequest

LINE_PURPOSE = "credit line"


def reserved_offer(amount: float, already_reserved: bool) -> float:
    """What a lender puts up of `amount` once the reserve lenders keep back is held out. A lender that has already held its
    reserve against what it takes in (a bank, against its deposits) is not cut twice."""
    return amount if already_reserved else capital_market.lendable_capacity(amount)


def hold_reserve(offers: Sequence[FundsOffer], already_reserved: Iterable[AgentId] = ()) -> List[FundsOffer]:
    """The offers with the reserve lenders keep back held out (`reserved_offer`)."""
    skipped = set(already_reserved)
    return [replace(offer, amount=reserved_offer(offer.amount, offer.lender in skipped)) for offer in offers]


def line_ceiling(market_rate: float, line: float) -> float:
    """The most a borrower of a line of `line` pays: the market rate plus the premium on the line itself, which is the
    security it shows (the one risk premium every loan is priced by)."""
    return market_rate + credit.risk_premium(line, line, 0.0)


def line_request(borrower: AgentId, currency: CurrencyId, line: float, market_rate: float) -> LoanRequest:
    """A request for a credit line of `line` at the most a line pays (`line_ceiling`)."""
    return LoanRequest(borrower, currency, line, line_ceiling(market_rate, line), 1.0, line, LINE_PURPOSE)


def actor_fundable(amount: float, existing_debt: float, collateral_value: float, arrears: float, market_rate: float,
                   lowest_ask: float) -> float:
    """The most of a draw of `amount` an actor (a state, a firm, a player) is lent: the same rule the clearing applies to
    every request, `credit_cap.fundable_amount` at the line's ceiling, with the economy's `credit.risk_premium` and the
    lowest rate any lender asks. Units are the economy's."""
    return credit_cap.fundable_amount(amount, existing_debt, collateral_value, arrears, line_ceiling(market_rate, amount),
                                      max(0.0, lowest_ask), credit.risk_premium)


@dataclass(frozen=True)
class LenderStanding:
    """One lender of the last lending: what it can still lend (its offer after the reserve it keeps back, less what the year's
    loans took, and for a bank no more than the cash it holds beyond its reserve, which its depositors' pledged funds do not
    add to), what its account holds now and the lowest rate it asked (the economy's units). `kind` is cohort, bank or fund."""
    lender: AgentId
    kind: str
    offered: float
    balance: float
    ask: float


def lender_standings(record, currency: CurrencyId) -> List[LenderStanding]:
    """The lenders of the last lending, cheapest ask first (ties by id)."""
    banks_by_id = record.capital_markets.banks
    standings = []
    for lender, offered in record.credit.offered_by_lender.items():
        bank = banks_by_id.get(lender)
        capacity = reserved_offer(offered, bank is not None)
        if bank is not None:
            capacity = min(capacity, banks.free_cash(record, bank, currency))
        capacity = max(0.0, capacity - record.credit.lent_by_lender.get(lender, 0.0))
        standings.append(LenderStanding(lender, "cohort" if lender in record.cohorts else "bank" if bank is not None else "fund",
                                        capacity, record.book.balance(lender, currency), record.credit.ask_by_lender[lender]))
    return sorted(standings, key=lambda each: (each.ask, each.lender))


def split_lines(loans: Sequence[Loan], line_borrowers: Iterable[AgentId]) -> Tuple[List[Loan], Dict[AgentId, float]]:
    """(the loans to book, what each line borrower was granted). A line's grant is a room, not a disbursement."""
    lines = set(line_borrowers)
    booked = [loan for loan in loans if loan.borrower not in lines]
    granted: Dict[AgentId, float] = {}
    for loan in loans:
        if loan.borrower in lines:
            granted[loan.borrower] = granted.get(loan.borrower, 0.0) + loan.principal
    return booked, granted
