"""`credit.clear_with_cause` and its helpers as they were written over request, offer and loan objects: the reference the clearing
kernel is tested against (`test_loans_clearing_kernel`). Do not use them in the game."""
from dataclasses import dataclass, field
import math
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from sim.economy import bank_credit_risk, credit_cap, credit_rate
from sim.economy.credit import ARREARS_PREMIUM, RATE_ADJUSTMENT_SHARE_PER_YEAR
from sim.economy.order_book import Entry, allocate_in_order, sticky_move
from sim.economy.replaced import replaced
from sim.economy.types import AgentId, CurrencyId, FundsOffer, Loan, LoanRequest


def risk_premium(debt_after: float, collateral_value: float, arrears_history: float) -> float:
    """Rate added to the base rate: a markup on the borrower's default probability (its debt against its collateral,
    taken as its equity; bank_credit_risk, after Eurace Bank_decide_credit_conditions) and a term in unpaid arrears."""
    if debt_after <= 0:
        return 0.0
    probability = bank_credit_risk.default_probability(debt_after, 0.0, collateral_value)
    arrears_share = min(1.0, max(0.0, arrears_history) / debt_after)
    return bank_credit_risk.markup(probability) + ARREARS_PREMIUM * arrears_share


def earnable_rate(gain: float, outlay: float = 1.0) -> float:
    """The most a borrower can pay per unit borrowed: what the loan earns it, `gain`, over the `outlay` it funds.
    Nothing when the outlay or the gain is not a finite positive figure, so a missing or runaway figure cannot
    become an unbounded cap."""
    if not (math.isfinite(gain) and math.isfinite(outlay)) or gain <= 0.0 or outlay <= 0.0:
        return 0.0
    return gain / outlay


NO_OFFER_AT_RATE = "no_offer_at_rate"      # every offer asks more than the bound lets the rate reach
NO_OFFERS = "no_offers"
NO_BORROWER_AT_ASK = "no_borrower_at_ask"      # no request can pay what the cheapest lender asks


@dataclass(frozen=True)
class LoanClearing:
    loans: List[Loan]
    rate: Optional[float]                # the base rate the loans were struck at; where nothing cleared, the rate held
                                         # from the last clearing (None when there was none), never a bid or an ask
    unmet: List[LoanRequest]
    cause: Optional[str] = None          # why nothing could clear, when nothing did
    limited: Mapping[AgentId, str] = field(default_factory=dict)   # borrowers funded for less than they asked, and why (credit_cap)


def clear(requests: Sequence[LoanRequest], offers: Sequence[FundsOffer], currency: CurrencyId,
          last_rate: Optional[float], existing_debt_by_borrower: Mapping[AgentId, float],
          arrears_by_borrower: Optional[Mapping[AgentId, float]] = None, year: int = 0,
          rate_ceiling: Optional[float] = None, expected_inflation: float = 0.0, clearing: str = "year",
          ) -> Tuple[List[Loan], Optional[float], List[LoanRequest]]:
    """`clear_with_cause` without the cause."""
    result = clear_with_cause(requests, offers, currency, last_rate, existing_debt_by_borrower, arrears_by_borrower,
                              year, rate_ceiling, expected_inflation, clearing)
    return result.loans, result.rate, result.unmet


def clear_with_cause(requests: Sequence[LoanRequest], offers: Sequence[FundsOffer], currency: CurrencyId,
                     last_rate: Optional[float], existing_debt_by_borrower: Mapping[AgentId, float],
                     arrears_by_borrower: Optional[Mapping[AgentId, float]] = None, year: int = 0,
                     rate_ceiling: Optional[float] = None, expected_inflation: float = 0.0,
                     clearing: str = "year") -> LoanClearing:
    """Match funds with requests. Returns the new loans, the base rate, the requests left unmet and a cause.

    A loan's id names the currency, the year and the `clearing` it came from, so two clearings that carry one year (the
    year's own and the next year's working capital) never give two loans one id.

    A request left unmet is returned with `amount` reduced to what it did not get. Each loan carries the
    base rate plus its borrower's premium; `disbursements(loans)` gives the money to move. `rate_ceiling`
    bounds the real rate: the base rate never passes it plus `expected_inflation`. Where that bound holds the
    rate below the clearing point, lenders are rationed by quantity: funds go to the borrowers whose premium
    (leverage, arrears, collateral) is least first. When every offer asks more than the bound, nothing can
    clear: the rate stays at its last value (the lowest ask when there is none) and the cause is
    `no_offer_at_rate`; the bound is never turned into a rate no lender accepts.
    """
    arrears_by_borrower = arrears_by_borrower or {}
    requests = sorted((request for request in requests if request.currency == currency and request.amount > 0),
                      key=lambda r: (r.borrower, r.purpose, r.amount, r.maximum_rate))
    offers = [offer for offer in offers if offer.currency == currency and offer.amount > 0]
    if not offers:
        return LoanClearing([], last_rate, list(requests), NO_OFFERS)      # borrowers' bids alone are not a price
    asked_amount: Dict[int, float] = {}    # position in `requests` -> the amount asked, for a request cut to what its collateral bears
    limited: Dict[AgentId, str] = {}
    lowest_offered = min(offer.minimum_rate for offer in offers)
    cut = []
    for position, request in enumerate(requests):
        # a request the premium on its whole amount prices out is funded for the most its collateral bears
        taken = credit_cap.fundable_amount(request.amount, existing_debt_by_borrower.get(request.borrower, 0.0),
                                           request.collateral_value, arrears_by_borrower.get(request.borrower, 0.0),
                                           request.maximum_rate, max(0.0, lowest_offered), risk_premium)
        if 0.0 < taken < request.amount:
            asked_amount[position] = request.amount
            limited[request.borrower] = credit_cap.COLLATERAL_BOUND
            request = replaced(request, amount=taken)
        cut.append(request)
    requests = cut
    premiums = [risk_premium(existing_debt_by_borrower.get(request.borrower, 0.0) + request.amount,
                             request.collateral_value, arrears_by_borrower.get(request.borrower, 0.0))
                for request in requests]
    default_probabilities = [bank_credit_risk.default_probability(existing_debt_by_borrower.get(request.borrower, 0.0),
                                                                 request.amount, request.collateral_value)
                             for request in requests]
    ceilings = [request.maximum_rate - premium for request, premium in zip(requests, premiums)]
    # a request whose ceiling is below zero or below every lender's ask cannot borrow at any rate the
    # market could clear at: it is rationed demand, left out of the clearing and returned as unmet
    lowest_ask = min((offer.minimum_rate for offer in offers), default=None)
    entry_floor = max(0.0, lowest_ask) if lowest_ask is not None else 0.0
    able = [ceiling >= entry_floor for ceiling in ceilings]
    target = credit_rate.base_rate_target([(offer.minimum_rate, offer.amount) for offer in offers],
                                          [(ceiling, request.amount) for ceiling, request, can in zip(ceilings, requests, able)
                                           if can])
    base_rate = sticky_move(last_rate, target, RATE_ADJUSTMENT_SHARE_PER_YEAR)
    if lowest_ask is not None and base_rate < lowest_ask <= max(ceilings, default=-math.inf):
        base_rate = lowest_ask      # a rate below every ask lends nothing while a borrower would pay the ask
    if not any(able):       # lenders alone are not a price: the rate still drifts toward the lowest ask
        return LoanClearing([], max(0.0, base_rate), list(requests), NO_BORROWER_AT_ASK)
    nominal_ceiling = None if rate_ceiling is None else rate_ceiling + max(0.0, expected_inflation)
    rationed_by_risk = nominal_ceiling is not None and base_rate > nominal_ceiling
    if rationed_by_risk:
        if lowest_ask is not None and lowest_ask > nominal_ceiling:
            # no lender accepts the bound: hold the rate, lend nothing, say why
            held = last_rate if last_rate is not None else lowest_ask
            return LoanClearing([], max(0.0, held), list(requests), NO_OFFER_AT_RATE)
        base_rate = nominal_ceiling
    base_rate = max(0.0, base_rate)
    lending =[offer for offer in offers if offer.minimum_rate <= base_rate]
    asking = [index for index, ceiling in enumerate(ceilings) if ceiling >= base_rate]
    supply = sum(offer.amount for offer in sorted(lending, key=lambda o: (o.lender, o.amount)))
    demand = sum(requests[index].amount for index in asking)
    lent = min(supply, demand)
    lender_entries: List[Entry] = [(offer.minimum_rate, offer.lender, offer.amount) for offer in lending]
    if rationed_by_risk:      # the least risky borrower is served first
        borrower_entries: List[Entry] = [(premiums[index], requests[index].borrower, requests[index].amount)
                                         for index in asking]
    else:
        borrower_entries = [(ceilings[index], requests[index].borrower, requests[index].amount) for index in asking]
    lender_amounts = allocate_in_order(lender_entries, lent, descending=False)
    borrower_amounts = allocate_in_order(borrower_entries, lent, descending=not rationed_by_risk)
    # lenders in cheapest-first order, then the same order of borrowers; a lender with a risk capacity (a bank's
    # headroom, Eurace Bank_decide_credit_conditions EXCESS_VAR) refuses whole any piece whose value at risk exceeds
    # what it has left, and keeps the rest for smaller pieces
    lender_queue = [[offer.lender, amount, offer.risk_capacity] for offer, amount in
                    sorted(((offer, amount) for offer, amount in zip(lending, lender_amounts) if amount > 0),
                           key=lambda pair: (pair[0].minimum_rate, pair[0].lender, pair[1]))]
    granted = dict(zip(asking, borrower_amounts))
    loans: List[Loan] = []
    for index in sorted(granted, key=lambda i: (-ceilings[i], requests[i].borrower, i)):
        request, owed = requests[index], granted[index]
        granted[index] = 0.0
        for entry in lender_queue:
            if owed <= 1e-12:
                break
            piece = min(owed, entry[1])
            if piece <= 1e-12:
                continue
            if entry[2] is not None:
                piece_at_risk = default_probabilities[index] * piece
                if piece_at_risk > entry[2] + 1e-12:
                    continue
                entry[2] -= piece_at_risk
            loans.append(Loan(
                contract_id="loan:%s:%d:%s:%d" % (currency, year, clearing, len(loans)), lender=entry[0],
                borrower=request.borrower, currency=currency, principal=piece,
                rate=base_rate + premiums[index], years_left=request.years,
                collateral_value=request.collateral_value * piece / request.amount, issued_year=year,
                collateral_tile=request.collateral_tile,
                collateral_share=request.collateral_share * piece / request.amount))
            owed -= piece
            entry[1] -= piece
            granted[index] += piece
    unmet = []
    for index, request in enumerate(requests):
        left = asked_amount.get(index, request.amount) - granted.get(index, 0.0)
        if left > 1e-9:
            unmet.append(replaced(request, amount=left))
    return LoanClearing(loans, base_rate, unmet, limited=limited)
