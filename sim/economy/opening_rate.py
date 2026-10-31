"""The rate the opening solves for credit: lenders' lowest asks against what borrowers can pay, cleared as the credit market clears.

The civilisation's typed `starting_interest_rate` is a historical reference (`against_history`), not an input.
"""
from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from . import credit, lender_ask
from .households_orders import HOUSEHOLD_TIME_PREFERENCE
from .market_memory import OPENING_EXPECTED_INFLATION
from .types import FundsOffer, LoanRequest

OPENING_CURRENCY = "opening"
# (lender id, time preference, expected inflation, funds offered)
OpeningLender = Tuple[str, float, float, float]


@dataclass(frozen=True)
class OpeningRate:
    rate: float
    cause: Optional[str]      # why the credit clearing did not set the rate, when it did not


def solved_opening_rate(lenders: Sequence[OpeningLender], requests: Sequence[LoanRequest]) -> OpeningRate:
    """The opening's rate: the credit market's clearing of the lenders' offers (each at its lowest ask, no loss
    history yet) against the requests. Where nobody lends or nobody borrows at the opening there is nothing to clear
    and the rate is the lenders' lowest ask: what the cheapest lender would take, never a borrower's bid."""
    asks = [(name, lender_ask.lowest_ask(time_preference, inflation), funds)
            for name, time_preference, inflation, funds in lenders]
    if not asks:
        raise ValueError("an opening needs at least one lender to ask a rate")
    offers = [FundsOffer(name, OPENING_CURRENCY, funds, ask) for name, ask, funds in asks if funds > 0.0]
    requests = [request for request in requests if request.currency == OPENING_CURRENCY]
    result = credit.clear_with_cause(requests, offers, OPENING_CURRENCY, None, {})
    if result.loans and result.rate is not None:
        return OpeningRate(result.rate, None)
    return OpeningRate(min(ask for _name, ask, _funds in asks), result.cause or credit.NO_OFFERS)


def opening_market_rate() -> float:
    """The rate the opening holds until the agent credit market first clears: households are the lenders, at their
    time preference and the expected inflation they open with; the resting opening gives them no spare cash and no
    borrower has asked yet, so it is their lowest ask."""
    return solved_opening_rate([("households", HOUSEHOLD_TIME_PREFERENCE, OPENING_EXPECTED_INFLATION, 0.0)], []).rate


def against_history(solved_rate: float, historical_rate: float) -> dict:
    """The solved rate beside the civilisation's typed historical one, for the opening's checks."""
    return {"solved": solved_rate, "historical": historical_rate,
            "ratio": solved_rate / historical_rate if historical_rate > 0.0 else None}
