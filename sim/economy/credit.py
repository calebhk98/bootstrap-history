"""The credit market for one currency: funds offered meet loans asked, and loans are serviced or defaulted.

Lenders offer funds at the lowest rate they take; a borrower asks at most a maximum rate and pays the base
rate plus a premium for its own leverage and arrears, so a risky borrower may be unable to borrow at any
rate (credit rationing). A default ends the loan without moving money: the lender's claim, which
credit_claims counts in its wealth, is lost and the borrower's debt is gone. A lender with less income and
wealth spends and lends less, and may itself fall behind on what it owes, so a cascade follows from
ordinary rules; credit_claims also keeps the defaulter's record for the next premium.
"""
from dataclasses import dataclass, replace
import math
from typing import List, Mapping, Optional, Sequence, Tuple

from sim.constants import declare

from .labour import Entry, allocate_in_order, clearing_point, sticky_move
from .types import AgentId, CurrencyId, FundsOffer, Loan, LoanRequest, Transfer

RATE_ADJUSTMENT_SHARE_PER_YEAR = declare(
    "RATE_ADJUSTMENT_SHARE_PER_YEAR", 0.3, kind="temporary_heuristic",
    unit="share of the gap to the clearing rate closed in a year", source=None, confidence="D",
    why="Lenders reprice slowly: standing loans and custom keep the base rate from jumping to the "
        "clearing level. Stands in for contract terms and lenders' search, which are not modelled.")
LEVERAGE_PREMIUM = declare(
    "LEVERAGE_PREMIUM", 0.2, kind="temporary_heuristic",
    unit="rate added at all debt and no collateral", source=None, confidence="D",
    why="Shape of the risk premium: grows with debt's share of debt plus collateral. Stands in for "
        "lenders' own estimate of loss given default, which needs a model of recovery that is absent.")
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
    """Rate added to the base rate: rises with debt against collateral and with unpaid arrears."""
    if debt_after <= 0:
        return 0.0
    leverage = debt_after / (debt_after + max(0.0, collateral_value))
    arrears_share = min(1.0, max(0.0, arrears_history) / debt_after)
    return LEVERAGE_PREMIUM * leverage + ARREARS_PREMIUM * arrears_share


def clear(requests: Sequence[LoanRequest], offers: Sequence[FundsOffer], currency: CurrencyId,
          last_rate: Optional[float], existing_debt_by_borrower: Mapping[AgentId, float],
          arrears_by_borrower: Optional[Mapping[AgentId, float]] = None, year: int = 0,
          rate_ceiling: Optional[float] = None) -> Tuple[List[Loan], float, List[LoanRequest]]:
    """Match funds with requests. Returns (new loans, base rate, requests left unmet).

    A request left unmet is returned with `amount` reduced to what it did not get. Each loan carries the
    base rate plus its borrower's premium; `disbursements(loans)` gives the money to move. The base rate
    never passes `rate_ceiling`: when funds are scarce the rest is rationed, not priced without bound.
    """
    arrears_by_borrower = arrears_by_borrower or {}
    requests = sorted((request for request in requests if request.currency == currency and request.amount > 0),
                      key=lambda r: (r.borrower, r.purpose, r.amount, r.maximum_rate))
    offers = [offer for offer in offers if offer.currency == currency and offer.amount > 0]
    premiums = [risk_premium(existing_debt_by_borrower.get(request.borrower, 0.0) + request.amount,
                             request.collateral_value, arrears_by_borrower.get(request.borrower, 0.0))
                for request in requests]
    ceilings = [request.maximum_rate - premium for request, premium in zip(requests, premiums)]
    target = clearing_point([(offer.minimum_rate, offer.amount) for offer in offers],
                            [(ceiling, request.amount) for ceiling, request in zip(ceilings, requests)])
    if target is None:
        base_rate = last_rate if last_rate is not None else 0.0
    else:
        base_rate = sticky_move(last_rate, target, RATE_ADJUSTMENT_SHARE_PER_YEAR)
        lowest_ask = min((offer.minimum_rate for offer in offers), default=None)
        if lowest_ask is not None and base_rate < lowest_ask <= max(ceilings, default=-math.inf):
            # a sticky rate below every lender's ask would lend nothing while a borrower would pay it
            base_rate = lowest_ask
    if rate_ceiling is not None:
        base_rate = min(base_rate, rate_ceiling)
    lending =[offer for offer in offers if offer.minimum_rate <= base_rate]
    asking = [index for index, ceiling in enumerate(ceilings) if ceiling >= base_rate]
    supply = sum(offer.amount for offer in sorted(lending, key=lambda o: (o.lender, o.amount)))
    demand = sum(requests[index].amount for index in asking)
    lent = min(supply, demand)
    lender_entries: List[Entry] = [(offer.minimum_rate, offer.lender, offer.amount) for offer in lending]
    borrower_entries: List[Entry] = [(ceilings[index], requests[index].borrower, requests[index].amount)
                                     for index in asking]
    lender_amounts = allocate_in_order(lender_entries, lent, descending=False)
    borrower_amounts = allocate_in_order(borrower_entries, lent, descending=True)
    # lenders in cheapest-first order, then the same order of borrowers, paired by running through both
    lender_queue = sorted(((offer.minimum_rate, offer.lender, amount)
                           for offer, amount in zip(lending, lender_amounts) if amount > 0))
    granted = dict(zip(asking, borrower_amounts))
    loans: List[Loan] = []
    position = 0
    lender_left = lender_queue[0][2] if lender_queue else 0.0
    for index in sorted(granted, key=lambda i: (-ceilings[i], requests[i].borrower, i)):
        request, owed = requests[index], granted[index]
        while owed > 1e-12 and position < len(lender_queue):
            piece = min(owed, lender_left)
            loans.append(Loan(
                loan_id="loan:%s:%d:%d" % (currency, year, len(loans)), lender=lender_queue[position][1],
                borrower=request.borrower, currency=currency, principal=piece,
                rate=base_rate + premiums[index], years_left=request.years,
                collateral_value=request.collateral_value * piece / request.amount, issued_year=year))
            owed -= piece
            lender_left -= piece
            if lender_left <= 1e-12:
                position += 1
                lender_left = lender_queue[position][2] if position < len(lender_queue) else 0.0
    unmet = []
    for index, request in enumerate(requests):
        left = request.amount - granted.get(index, 0.0)
        if left > 1e-9:
            unmet.append(replace(request, amount=left))
    return loans, base_rate, unmet


def disbursements(loans: Sequence[Loan]) -> List[Transfer]:
    """The money each new loan moves from lender to borrower."""
    return [Transfer(loan.lender, loan.borrower, loan.currency, loan.principal,
                     "loan_disbursement:" + loan.loan_id) for loan in loans]


def service(loans: Sequence[Loan], cash_by_borrower: Mapping[AgentId, float], year: int,
            ) -> Tuple[List[Transfer], List[Loan], List[Default]]:
    """Collect one year's interest and principal installment, borrower to lender.

    A borrower pays loans in id order until its cash runs out; what it cannot pay joins the loan's arrears,
    which are collected first next year. Arrears past the declared share of principal end the loan: it is
    removed, no money moves, and the loss is recorded. Repaid loans are removed.
    """
    cash = dict(cash_by_borrower)
    transfers: List[Transfer] = []
    updated: List[Loan] = []
    defaults: List[Default] = []
    for loan in sorted(loans, key=lambda l: l.loan_id):
        installment = loan.principal if loan.years_left <= 1.0 else loan.principal / loan.years_left
        due = loan.arrears + loan.principal * loan.rate + installment
        paid = min(max(0.0, cash.get(loan.borrower, 0.0)), due)
        if paid > 0:
            cash[loan.borrower] = cash.get(loan.borrower, 0.0) - paid
            transfers.append(Transfer(loan.borrower, loan.lender, loan.currency, paid,
                                      "loan_service:%s:%d" % (loan.loan_id, year)))
        arrears = due - paid
        principal = loan.principal - installment
        if arrears > DEFAULT_ARREARS_SHARE * loan.principal + 1e-12:
            defaults.append(Default(loan.loan_id, loan.lender, loan.borrower, loan.currency,
                                    loss=principal + arrears))
            continue
        if principal <= 1e-12 and arrears <= 1e-12:
            continue
        updated.append(replace(loan, principal=principal, arrears=arrears,
                               years_left=max(0.0, loan.years_left - 1.0)))
    return transfers, updated, defaults
