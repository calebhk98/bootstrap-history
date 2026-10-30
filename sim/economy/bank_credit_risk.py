"""A bank's credit risk after Eurace@Unibi: a borrower's default probability from its leverage, the value at risk of
the loans a bank holds, the headroom its equity allows, and the rate markup on a risky borrower.

Follows Credit/Bank_Credit_Functions.c in the Eurace@Unibi source (Bank_rank_credit_requests for the default
probability and the value at risk of a request, Bank_decide_credit_conditions for the headroom ALFA * EQUITY - VALUE_AT_RISK
and the markup on the base rate). Eurace's base rate is the central bank's constant; here the base is the lenders' own
lowest ask (clear in credit.py), so only the markup is ported.
"""
import math
from typing import Iterable, List, Mapping, Tuple

from sim.constants import declare

# Eurace: Bank_rank_credit_requests uses multiplicator = 0.10 in the C; the user manual (ch. 7) omits it.
DEFAULT_PROBABILITY_SENSITIVITY = declare(
    "DEFAULT_PROBABILITY_SENSITIVITY", 0.10, kind="temporary_heuristic",
    unit="share of (debt + request) / equity entering the default probability exponent", source=None, confidence="D",
    retire="Complaints/106: a bank estimates a borrower's default from the losses its own loan record shows",
    why="Eurace@Unibi Bank_rank_credit_requests: default probability 1 - exp(-0.10 * (debt + request) / equity). The "
        "0.10 is Eurace's; no source for it in this setting.")
# Eurace: ALFA in Credit/model.xml ("Basel II regulatory parameter, default 10"), used by Bank_decide_credit_conditions.
BANK_ALFA = declare(
    "BANK_ALFA", 10.0, kind="temporary_heuristic",
    unit="multiple of its equity a bank's value at risk may reach", source=None, confidence="D",
    retire="Complaints/106: a bank sizes its risk to the losses its capital can bear",
    why="Eurace@Unibi ALFA: banks lend while the value at risk of their loans stays within ALFA * EQUITY. "
        "Stands in for a regulator's or owners' limit, which is not modelled.")
# Eurace: BANK_LAMBDA in Bank_decide_credit_conditions, interest = ECB_INTEREST_RATE * (1 + BANK_LAMBDA * bankruptcy_prob + U).
BANK_LAMBDA = declare(
    "BANK_LAMBDA", 3.0, kind="temporary_heuristic",
    unit="markup, as a multiple of the base rate, at certain default", source=None, confidence="D",
    retire="Complaints/106: a bank prices default from the loss it expects, not a weight on its probability",
    why="Eurace@Unibi BANK_LAMBDA (3.0 in the C comment): the rate is the base times (1 + BANK_LAMBDA * default "
        "probability + a uniform draw). The uniform draw is not ported: a draw would make the loan depend on call order.")
MARKUP_REFERENCE_RATE = declare(
    "MARKUP_REFERENCE_RATE", 0.07, kind="temporary_heuristic",
    unit="the base rate the markup is a multiple of, per year", source=None, confidence="D",
    retire="Complaints/106: the markup scales with the cleared base rate of the credit market",
    why="risk_premium is asked by callers that hold no cleared base rate yet (the ceiling is set before the rate "
        "is), so the markup BANK_LAMBDA * probability multiplies this fixed reference, not the base rate Eurace uses.")


def default_probability(debt: float, request: float, equity: float) -> float:
    """1 - exp(-sensitivity * (debt + request) / equity); one where the borrower has no equity, nothing for no debt.
    Follows Eurace Bank_rank_credit_requests."""
    owed = max(0.0, debt) + max(0.0, request)
    if owed <= 0.0:
        return 0.0
    if equity <= 0.0:
        return 1.0
    return 1.0 - math.exp(-DEFAULT_PROBABILITY_SENSITIVITY * owed / equity)


def value_at_risk(exposures: Iterable[Tuple[float, float]]) -> float:
    """Sum of principal times default probability over (principal, probability) pairs. Follows Eurace's
    VALUE_AT_RISK, the sum of each loan's value at risk."""
    return sum(max(0.0, principal) * probability for principal, probability in exposures)


def exposures(loans: Iterable, debt_by_borrower: Mapping[str, float]) -> List[Tuple[float, float]]:
    """(principal, default probability) for each loan a bank holds, the probability from the borrower's total debt
    against the collateral pledged to the loan, taken as the borrower's equity."""
    return [(loan.principal, default_probability(debt_by_borrower.get(loan.borrower, loan.principal), 0.0,
                                                 loan.collateral_value)) for loan in loans]


def var_headroom(equity: float, current_value_at_risk: float) -> float:
    """Value at risk the bank may still take on: ALFA * equity less what it carries, never below nothing. Follows
    Eurace Bank_decide_credit_conditions (EXCESS_VAR)."""
    return max(0.0, BANK_ALFA * max(0.0, equity) - current_value_at_risk)


def markup(probability: float) -> float:
    """The rate added for default risk: BANK_LAMBDA * probability * the reference rate. Follows Eurace
    Bank_decide_credit_conditions, ECB_INTEREST_RATE * BANK_LAMBDA * bankruptcy_prob."""
    return BANK_LAMBDA * probability * MARKUP_REFERENCE_RATE
