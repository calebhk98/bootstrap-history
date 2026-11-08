"""The credit market's clearing for one currency: requests and offers are packed into tables, `sim/loans/clearing_kernel.py` clears
them, and the answer is read back as the `LoanClearing` the callers take (loans as `Contract`s, the requests left unmet, the base
rate, the cause when nothing cleared, the borrowers funded for less than they asked).

The rules are those of `credit.clear_with_cause`'s docstring; the Python they were first written in is kept for the tests in
`sim/tests/credit_clear_plain.py`."""
from typing import Dict, List, Mapping, Optional, Sequence

import numpy

from sim.contract_record import Contract
from sim.loans.clearing_kernel import TABLE_FULL, clear_loans
from sim.loans.clearing_tables import (CLEARED, NEW_LOANS, NO_BORROWER_AT_ASK, NO_OFFER_AT_RATE, OFFERS, REQUESTS, NewLoans, Offers,
                                       Requests)

from . import bank_credit_risk, credit, credit_cap, credit_rate
from .replaced import replaced
from .types import AgentId, CurrencyId, FundsOffer, LoanRequest

CAUSE_OF = {NO_BORROWER_AT_ASK: credit.NO_BORROWER_AT_ASK, NO_OFFER_AT_RATE: credit.NO_OFFER_AT_RATE}
ROOM_STEP = 4        # a loans table that proves too small is made this many times bigger and the clearing run again


def constants() -> numpy.ndarray:
    """The declared numbers the kernel uses, in the order of `clearing_tables.CONSTANT_NAMES`."""
    return numpy.array([bank_credit_risk.DEFAULT_PROBABILITY_SENSITIVITY, bank_credit_risk.BANK_LAMBDA,
                        bank_credit_risk.MARKUP_REFERENCE_RATE, credit.ARREARS_PREMIUM, credit.RATE_ADJUSTMENT_SHARE_PER_YEAR,
                        credit_rate.MATERIAL_LENDER_SHARE, credit_cap.BISECTION_STEPS], dtype=numpy.float64)


def ranks_of(names: Sequence[str]) -> List[int]:
    """The place of each name when the distinct names are sorted."""
    place = {name: rank for rank, name in enumerate(sorted(set(names)))}
    return [place[name] for name in names]


def request_table(requests: Sequence[LoanRequest], debt: Mapping[AgentId, float], arrears: Mapping[AgentId, float]) -> Requests:
    table = REQUESTS.new_table(Requests, len(requests), len(requests))
    ranks = ranks_of([request.borrower for request in requests])
    for row, request in enumerate(requests):
        table.borrower_rank[row] = ranks[row]
        table.amount[row], table.maximum_rate[row], table.years[row] = request.amount, request.maximum_rate, request.years
        table.collateral_value[row], table.collateral_share[row] = request.collateral_value, request.collateral_share
        table.existing_debt[row] = debt.get(request.borrower, 0.0)
        table.arrears_history[row] = arrears.get(request.borrower, 0.0)
    return table


def offer_table(offers: Sequence[FundsOffer]) -> Offers:
    table = OFFERS.new_table(Offers, len(offers), len(offers))
    ranks = ranks_of([offer.lender for offer in offers])
    for row, offer in enumerate(offers):
        table.lender_rank[row], table.amount[row], table.minimum_rate[row] = ranks[row], offer.amount, offer.minimum_rate
        table.has_capacity[row] = offer.risk_capacity is not None
        table.risk_capacity[row] = offer.risk_capacity if offer.risk_capacity is not None else 0.0
    return table


_KEPT_LOANS = []        # the loans table of the last clearing, reused while it is big enough (a clearing's loans are read before the next)


def _loans_table(room: int) -> NewLoans:
    """An empty loans table with room for `room` loans."""
    if not _KEPT_LOANS or len(_KEPT_LOANS[0].principal) < room:
        _KEPT_LOANS[:] = [NEW_LOANS.new_table(NewLoans, room)]
    table = _KEPT_LOANS[0]
    table.row_count[0] = 0
    return table


def run_kernel(requests: Requests, offers: Offers, last_rate: Optional[float], rate_ceiling: Optional[float],
               expected_inflation: float):
    """(status, scalars, new loans): the clearing kernel run, on a loans table made bigger and run again if it was too small."""
    room = max(16, len(requests.amount) + len(offers.amount))
    while True:
        new_loans = _loans_table(room)
        scalars = numpy.zeros(2)
        status = clear_loans(requests, offers, constants(), 0.0 if last_rate is None else last_rate, last_rate is not None,
                             0.0 if rate_ceiling is None else rate_ceiling, rate_ceiling is not None, expected_inflation, new_loans, scalars)
        if status != TABLE_FULL:
            return status, scalars, new_loans
        room *= ROOM_STEP


def cut_requests(requests: Sequence[LoanRequest], table: Requests) -> List[LoanRequest]:
    """The requests as the clearing worked with them: a request cut to what its collateral bears carries that amount."""
    return [replaced(request, amount=float(table.funded_amount[row])) if table.funded_amount[row] < request.amount else request
            for row, request in enumerate(requests)]


def new_loan_objects(requests: Sequence[LoanRequest], offers: Sequence[FundsOffer], new_loans: NewLoans, currency: CurrencyId,
                     year: int, clearing: str) -> List[Contract]:
    """The loans struck, as contracts, in the order they were struck; ids name the currency, the year and the clearing."""
    loans = []
    for number in range(int(new_loans.row_count[0])):
        request, offer = requests[int(new_loans.request[number])], offers[int(new_loans.offer[number])]
        loans.append(Contract(
            contract_id="loan:%s:%d:%s:%d" % (currency, year, clearing, number), lender=offer.lender, borrower=request.borrower,
            currency=currency, principal=float(new_loans.principal[number]), rate=float(new_loans.rate[number]),
            years_left=request.years, collateral_value=float(new_loans.collateral_value[number]), issued_year=year,
            collateral_tile=request.collateral_tile, collateral_share=float(new_loans.collateral_share[number])))
    return loans


def clear_with_cause(requests: Sequence[LoanRequest], offers: Sequence[FundsOffer], currency: CurrencyId, last_rate: Optional[float],
                     existing_debt_by_borrower: Mapping[AgentId, float], arrears_by_borrower: Optional[Mapping[AgentId, float]] = None,
                     year: int = 0, rate_ceiling: Optional[float] = None, expected_inflation: float = 0.0, clearing: str = "year",
                     ) -> "credit.LoanClearing":
    """`credit.clear_with_cause`: match funds with requests; see its docstring for the rules."""
    arrears_by_borrower = arrears_by_borrower or {}
    requests = sorted((request for request in requests if request.currency == currency and request.amount > 0),
                      key=lambda request: (request.borrower, request.purpose, request.amount, request.maximum_rate))
    offers = [offer for offer in offers if offer.currency == currency and offer.amount > 0]
    if not offers:
        return credit.LoanClearing([], last_rate, list(requests), credit.NO_OFFERS)      # borrowers' bids alone are not a price
    table = request_table(requests, existing_debt_by_borrower, arrears_by_borrower)
    status, scalars, new_loans = run_kernel(table, offer_table(offers), last_rate, rate_ceiling, expected_inflation)
    cut = cut_requests(requests, table)
    limited: Dict[AgentId, str] = {request.borrower: credit_cap.COLLATERAL_BOUND for request, original in zip(cut, requests)
                                   if request is not original}
    rate = float(scalars[0]) if scalars[1] else None
    if status != CLEARED:
        return credit.LoanClearing([], rate, list(cut), CAUSE_OF[status])
    unmet = [replaced(request, amount=float(table.unmet[row])) for row, request in enumerate(requests) if table.unmet[row] > 0.0]
    return credit.LoanClearing(new_loan_objects(requests, offers, new_loans, currency, year, clearing), rate, unmet, limited=limited)

