"""How long the claims a lender holds run: the term of each loan on the book, weighted by what it is worth to its lender.

A lost claim was exposed for its whole life (`loss_memory.blend`). The default record carries no term, so the life is read
from the loans the lender still holds, else from the whole book, else it is unknown (None) and the caller says what it does.
"""
from typing import Dict, Iterable, Optional, Tuple

from sim.loans import reads
from sim.loans.view import LoanList

from .credit import DEFAULT_ARREARS_SHARE
from .credit_claims import claim_value, claims_by_lender
from .types import AgentId, CurrencyId, Loan


def _term_years(loan: Loan, year: int) -> float:
    return max(0.0, loan.years_left) + max(0, year - loan.issued_year)


def mean_term_years(loans: Iterable[Loan], year: int, currency: CurrencyId = None) -> Tuple[Dict[AgentId, float], Optional[float]]:
    """(each lender's claim-weighted mean loan term in years, the same over every claim on the book). A lender whose claims are
    worth nothing has no entry; the book mean is None when no claim is worth anything."""
    if isinstance(loans, LoanList):
        weighted = reads.claim_term_years_by_lender(loans.store, DEFAULT_ARREARS_SHARE, year, currency)
        claims = reads.claims_by_lender(loans.store, DEFAULT_ARREARS_SHARE, currency)
    else:
        selected = [loan for loan in loans if currency is None or loan.currency == currency]
        claims = claims_by_lender(selected)
        weighted: Dict[AgentId, float] = {}
        for loan in selected:
            weighted[loan.lender] = weighted.get(loan.lender, 0.0) + claim_value(loan) * _term_years(loan, year)
    by_lender = {agent: weighted[agent] / claims[agent] for agent in sorted(weighted) if claims.get(agent, 0.0) > 0.0}
    book_claims = sum(claims.values())
    book_mean = sum(weighted.values()) / book_claims if book_claims > 0.0 else None
    return by_lender, book_mean
