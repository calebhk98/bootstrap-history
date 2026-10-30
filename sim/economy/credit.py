"""The credit market for one currency: funds offered meet loans asked, and loans are serviced or defaulted.

Lenders offer funds at the lowest rate they take; a borrower asks at most a maximum rate and pays the base
rate plus a premium for its own leverage and arrears, so a risky borrower may be unable to borrow at any
rate (credit rationing). A default ends the loan without moving money: the lender's claim, which
credit_claims counts in its wealth, is lost and the borrower's debt is gone. A lender with less income and
wealth spends and lends less, and may itself fall behind on what it owes, so a cascade follows from
ordinary rules; credit_claims also keeps the defaulter's record for the next premium.
"""
from dataclasses import dataclass
import math
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from sim.constants import declare

from . import bank_credit_risk
from .labour import Entry, allocate_in_order, clearing_point, sticky_move
from .types import AgentId, CurrencyId, FundsOffer, Loan, LoanRequest, Transfer
from .replaced import replaced

RATE_ADJUSTMENT_SHARE_PER_YEAR = declare(
    "RATE_ADJUSTMENT_SHARE_PER_YEAR", 0.3, kind="temporary_heuristic",
    unit="share of the gap to the clearing rate closed in a year", source=None, confidence="D",
    why="Lenders reprice slowly: standing loans and custom keep the base rate from jumping to the "
        "clearing level. Stands in for contract terms and lenders' search, which are not modelled.")
ARREARS_PREMIUM = declare(
    "ARREARS_PREMIUM", 0.3, kind="temporary_heuristic",
    unit="rate added when arrears equal the whole debt", source=None, confidence="D",
    why="A borrower that has fallen behind is likelier to again; the premium grows with arrears as a "
        "share of debt. Stands in for lenders' learning about borrowers, which is not modelled.")
DEFAULT_ARREARS_SHARE = declare(
    "DEFAULT_ARREARS_SHARE", 0.5, kind="temporary_heuristic",
    unit="arrears as a share of the loan's principal before the year's payment", source=None,
    confidence="D",
    why="The point where a lender writes a loan off. Stands in for the enforcement institutions "
        "(courts, seizure, debt bondage) that decide how long arrears are tolerated, which are not modelled.")


@dataclass(frozen=True)
class Default:
    loan_id: str
    lender: AgentId
    borrower: AgentId
    currency: CurrencyId
    loss: float                  # principal and arrears the lender will never collect


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


def _funds_idle_above_clearing_rate(offers: Sequence[FundsOffer], requests: Sequence[LoanRequest],
                                    ceilings: Sequence[float], able: Sequence[bool], held_rate: float,
                                    clearing_rate: float) -> bool:
    """True when some borrower would pay the clearing rate and, at the held rate above it, lenders still
    have funds left over: the held rate is not a market-clearing price."""
    demand_at_clearing = sum(request.amount for request, ceiling, can in zip(requests, ceilings, able)
                             if can and ceiling >= clearing_rate)
    if demand_at_clearing <= 0.0:
        return False
    demand_at_held = sum(request.amount for request, ceiling in zip(requests, ceilings) if ceiling >= held_rate)
    supply_at_held = sum(offer.amount for offer in offers if offer.minimum_rate <= held_rate)
    return supply_at_held > demand_at_held


def _borrowers_rationed_below_clearing_rate(offers: Sequence[FundsOffer], ceilings: Sequence[float],
                                            able: Sequence[bool], requests: Sequence[LoanRequest],
                                            held_rate: float) -> bool:
    """True when, at the held rate, borrowers who would pay it ask for more than the lenders asking no more
    than it hold: the held rate is below the price at which supply meets demand."""
    demand_at_held = sum(request.amount for request, ceiling, can in zip(requests, ceilings, able)
                         if can and ceiling >= held_rate)
    supply_at_held = sum(offer.amount for offer in offers if offer.minimum_rate <= held_rate)
    return demand_at_held > supply_at_held


NO_OFFER_AT_RATE = "no_offer_at_rate"      # every offer asks more than the bound lets the rate reach
NO_OFFERS = "no_offers"
NO_BORROWER_AT_ASK = "no_borrower_at_ask"      # no request can pay what the cheapest lender asks


@dataclass(frozen=True)
class Clearing:
    loans: List[Loan]
    rate: Optional[float]                # the base rate the loans were struck at; where nothing cleared, the rate held
                                         # from the last clearing (None when there was none), never a bid or an ask
    unmet: List[LoanRequest]
    cause: Optional[str] = None          # why nothing could clear, when nothing did


def clear(requests: Sequence[LoanRequest], offers: Sequence[FundsOffer], currency: CurrencyId,
          last_rate: Optional[float], existing_debt_by_borrower: Mapping[AgentId, float],
          arrears_by_borrower: Optional[Mapping[AgentId, float]] = None, year: int = 0,
          rate_ceiling: Optional[float] = None, expected_inflation: float = 0.0,
          ) -> Tuple[List[Loan], Optional[float], List[LoanRequest]]:
    """`clear_with_cause` without the cause."""
    result = clear_with_cause(requests, offers, currency, last_rate, existing_debt_by_borrower, arrears_by_borrower,
                              year, rate_ceiling, expected_inflation)
    return result.loans, result.rate, result.unmet


def clear_with_cause(requests: Sequence[LoanRequest], offers: Sequence[FundsOffer], currency: CurrencyId,
                     last_rate: Optional[float], existing_debt_by_borrower: Mapping[AgentId, float],
                     arrears_by_borrower: Optional[Mapping[AgentId, float]] = None, year: int = 0,
                     rate_ceiling: Optional[float] = None, expected_inflation: float = 0.0) -> Clearing:
    """Match funds with requests. Returns the new loans, the base rate, the requests left unmet and a cause.

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
        return Clearing([], last_rate, list(requests), NO_OFFERS)      # borrowers' bids alone are not a price
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
    target = clearing_point([(offer.minimum_rate, offer.amount) for offer in offers],
                            [(ceiling, request.amount) for ceiling, request, can in zip(ceilings, requests, able)
                             if can])
    if not any(able):       # lenders alone are not a price either
        return Clearing([], last_rate, list(requests), NO_BORROWER_AT_ASK)
    base_rate = sticky_move(last_rate, target, RATE_ADJUSTMENT_SHARE_PER_YEAR)
    if lowest_ask is not None and base_rate < lowest_ask <= max(ceilings, default=-math.inf):
        # a sticky rate below every lender's ask would lend nothing while a borrower would pay it
        base_rate = lowest_ask
    elif base_rate > target and _funds_idle_above_clearing_rate(offers, requests, ceilings, able, base_rate, target):
        # repricing may be slow, but not so slow that funds sit unlent while a borrower pays the clearing rate
        base_rate = target
    elif base_rate < target and _borrowers_rationed_below_clearing_rate(offers, ceilings, able, requests, base_rate):
        # nor so slow that borrowers who would pay the clearing rate are turned away by a rate below the
        # ask of the lenders who would fund them
        base_rate = target
    nominal_ceiling = None if rate_ceiling is None else rate_ceiling + max(0.0, expected_inflation)
    rationed_by_risk = nominal_ceiling is not None and base_rate > nominal_ceiling
    if rationed_by_risk:
        if lowest_ask is not None and lowest_ask > nominal_ceiling:
            # no lender accepts the bound: hold the rate, lend nothing, say why
            held = last_rate if last_rate is not None else lowest_ask
            return Clearing([], max(0.0, held), list(requests), NO_OFFER_AT_RATE)
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
                contract_id="loan:%s:%d:%d" % (currency, year, len(loans)), lender=entry[0],
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
        left = request.amount - granted.get(index, 0.0)
        if left > 1e-9:
            unmet.append(replaced(request, amount=left))
    return Clearing(loans, base_rate, unmet)


def disbursements(loans: Sequence[Loan]) -> List[Transfer]:
    """The money each new loan moves from lender to borrower."""
    return [Transfer(loan.lender, loan.borrower, loan.currency, loan.principal,
                     "loan_disbursement:" + loan.loan_id) for loan in loans]


@dataclass
class Receipt:
    """What one lender received in a year: interest is income; principal and arrears (overdue principal)
    only turn a claim back into cash."""
    interest: float = 0.0
    principal: float = 0.0
    arrears: float = 0.0


def service(loans: Sequence[Loan], cash_by_borrower: Mapping[AgentId, float], year: int,
            ) -> Tuple[List[Transfer], List[Loan], List[Default]]:
    """`service_split` without the split of what each lender received."""
    transfers, updated, defaults, _receipts = service_split(loans, cash_by_borrower, year)
    return transfers, updated, defaults


def service_split(loans: Sequence[Loan], cash_by_borrower: Mapping[AgentId, float], year: int,
                  ) -> Tuple[List[Transfer], List[Loan], List[Default], Dict[AgentId, Receipt]]:
    """Collect one year's interest and principal installment, borrower to lender.

    A borrower pays loans in id order until its cash runs out; a payment clears, in turn, arrears interest,
    overdue principal, this year's interest and the installment. What it cannot pay joins the loan's
    arrears, which are collected first next year. Arrears past the declared share of principal end the
    loan: it is removed, no money moves, and the loss is recorded. Repaid loans are removed. The last
    result is each lender's receipt split into interest, principal and arrears.
    """
    cash = dict(cash_by_borrower)
    transfers: List[Transfer] = []
    updated: List[Loan] = []
    defaults: List[Default] = []
    receipts: Dict[AgentId, Receipt] = {}
    for loan in sorted(loans, key=lambda l: l.loan_id):
        installment = loan.principal if loan.years_left <= 1.0 else loan.principal / loan.years_left
        interest = loan.principal * loan.rate
        arrears_interest = min(loan.arrears, loan.arrears_interest)
        arrears_principal = loan.arrears - arrears_interest
        due = loan.arrears + interest + installment
        paid = min(max(0.0, cash.get(loan.borrower, 0.0)), due)
        if paid > 0:
            cash[loan.borrower] = cash.get(loan.borrower, 0.0) - paid
            transfers.append(Transfer(loan.borrower, loan.lender, loan.currency, paid,
                                      "loan_service:%s:%d" % (loan.loan_id, year)))
        left = paid
        paid_parts = []
        for part in (arrears_interest, arrears_principal, interest, installment):
            take = min(left, part)
            paid_parts.append(take)
            left -= take
        receipt = receipts.setdefault(loan.lender, Receipt())
        receipt.interest += paid_parts[0] + paid_parts[2]
        receipt.arrears += paid_parts[1]
        receipt.principal += paid_parts[3]
        arrears = due - paid
        principal = loan.principal - installment
        if arrears > DEFAULT_ARREARS_SHARE * loan.principal + 1e-12:
            defaults.append(Default(loan.loan_id, loan.lender, loan.borrower, loan.currency,
                                    loss=principal + arrears))
            continue
        if principal <= 1e-12 and arrears <= 1e-12:
            continue
        updated.append(replaced(loan, principal=principal, arrears=arrears,
                                arrears_interest=(arrears_interest - paid_parts[0]) + (interest - paid_parts[2]),
                                years_left=max(0.0, loan.years_left - 1.0)))
    return transfers, updated, defaults, receipts
