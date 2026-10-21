"""Credit lines in the clearing (Complaint 665). An actor whose money the engine keeps (the founder, any other
seat) asks the credit market for its line like every other borrower: its request joins `credit.clear`, ordered by
its ceiling, and what the clearing grants it is its room. No money moves in the economy's book for it, since its
purse is the engine's. The reserve lenders keep back is held out of every lender's offer alike.
"""
from dataclasses import replace
from typing import Dict, Iterable, List, Sequence, Tuple

from sim.world import capital_market

from . import credit
from .types import AgentId, CurrencyId, FundsOffer, Loan, LoanRequest

LINE_PURPOSE = "credit line"


def hold_reserve(offers: Sequence[FundsOffer], already_reserved: Iterable[AgentId] = ()) -> List[FundsOffer]:
    """The offers with the reserve lenders keep back held out. A lender that has already held its reserve
    against what it takes in (a bank, against its deposits) is not cut twice."""
    skipped = set(already_reserved)
    return [offer if offer.lender in skipped else replace(offer, amount=capital_market.lendable_capacity(offer.amount))
            for offer in offers]


def line_request(borrower: AgentId, currency: CurrencyId, line: float, market_rate: float) -> LoanRequest:
    """A request for a credit line of `line`: the borrower pays at most the market rate plus the whole premium
    its standing leaves at the limit, and the line itself is the security it shows."""
    ceiling = capital_market.borrower_rate(market_rate, 0.0, 1.0) + credit.risk_premium(line, line, 0.0)
    return LoanRequest(borrower, currency, line, ceiling, 1.0, line, LINE_PURPOSE)


def split_lines(loans: Sequence[Loan], line_borrowers: Iterable[AgentId]) -> Tuple[List[Loan], Dict[AgentId, float]]:
    """(the loans to book, what each line borrower was granted). A line's grant is a room, not a disbursement."""
    lines = set(line_borrowers)
    booked = [loan for loan in loans if loan.borrower not in lines]
    granted: Dict[AgentId, float] = {}
    for loan in loans:
        if loan.borrower in lines:
            granted[loan.borrower] = granted.get(loan.borrower, 0.0) + loan.principal
    return booked, granted
