"""The credit market for one currency: funds offered meet loans asked, and loans are serviced or defaulted.

Lenders offer funds at the lowest rate they take; a borrower asks at most a maximum rate and pays the base
rate plus a premium for its own leverage and arrears, so a risky borrower may be unable to borrow at any
rate (credit rationing). A default ends the loan without moving money: the lender's claim, which
credit_claims counts in its wealth, is lost and the borrower's debt is gone. A lender with less income and
wealth spends and lends less, and may itself fall behind on what it owes, so a cascade follows from
ordinary rules; credit_claims also keeps the defaulter's record for the next premium.
"""
from dataclasses import dataclass, field
import math
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from sim.constants import declare

from . import bank_credit_risk
from .types import AgentId, CurrencyId, FundsOffer, Loan, LoanRequest, Transfer

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
    from .credit_clearing import clear_with_cause as cleared      # the table kernel (sim/loans/clearing_kernel.py) behind this rule
    return cleared(requests, offers, currency, last_rate, existing_debt_by_borrower, arrears_by_borrower, year, rate_ceiling,
                   expected_inflation, clearing)


def disbursements(loans: Sequence[Loan]) -> List[Transfer]:
    """The money each new loan moves from lender to borrower."""
    return [Transfer(loan.lender, loan.borrower, loan.currency, loan.principal,
                     "loan_disbursement:" + loan.loan_id) for loan in loans]


def disbursement_rows(loans: Sequence[Loan]):
    """`disbursements` as the parallel lists `transfer_rows.post_payments` takes: (lenders, borrowers, currencies, amounts, purposes)."""
    return ([loan.lender for loan in loans], [loan.borrower for loan in loans], [loan.currency for loan in loans],
            [loan.principal for loan in loans], ["loan_disbursement:" + loan.loan_id for loan in loans])


@dataclass
class Receipt:
    """What one lender received in a year: interest is income; principal and arrears (overdue principal)
    only turn a claim back into cash."""
    interest: float = 0.0
    principal: float = 0.0
    arrears: float = 0.0


def installment_of(loan: Loan) -> float:
    """The principal a loan returns at the year's end: an even share over the years left, all of it in the last year. The one
    rule firms, banks and the yearly service all read."""
    return loan.principal if loan.years_left <= 1.0 else loan.principal / loan.years_left


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
    from .credit_service import service_split as served      # the table kernel (credit_service.py) over a table made from `loans`
    return served(loans, cash_by_borrower, year)
