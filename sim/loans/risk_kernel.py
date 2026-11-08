"""The price of a borrower's risk: its chance of default, the premium on its rate and the most it can be lent (Eurace@Unibi
Bank_decide_credit_conditions and Bank_rank_credit_requests; `sim/economy/bank_credit_risk.py` and `credit_cap.py` are the Python
these follow). The constants are passed in an array in the order of `clearing_tables.CONSTANT_NAMES`."""
import math

from sim.jit import njit

SENSITIVITY, LAMBDA, REFERENCE_RATE, ARREARS_PREMIUM, ADJUSTMENT_SHARE, MATERIAL_SHARE, BISECTION_STEPS = 0, 1, 2, 3, 4, 5, 6


@njit
def default_probability(debt, request, equity, constants):
    """1 - exp(-sensitivity * (debt + request) / equity); one for a borrower with no equity, nothing for no debt."""
    owed = max(0.0, debt) + max(0.0, request)
    if owed <= 0.0:
        return 0.0
    if equity <= 0.0:
        return 1.0
    return 1.0 - math.exp(-constants[SENSITIVITY] * owed / equity)


@njit
def risk_premium(debt_after, collateral_value, arrears_history, constants):
    """The rate added to the base rate: a markup on the default probability and a term in the arrears the market holds against
    the borrower, as a share of its debt."""
    if debt_after <= 0:
        return 0.0
    probability = default_probability(debt_after, 0.0, collateral_value, constants)
    arrears_share = min(1.0, max(0.0, arrears_history) / debt_after)
    return constants[LAMBDA] * probability * constants[REFERENCE_RATE] + constants[ARREARS_PREMIUM] * arrears_share


@njit
def meets_lowest_ask(taken, debt, collateral_value, arrears, maximum_rate, lowest_ask, constants):
    """Whether, borrowing `taken` on top of its debt, the borrower's ceiling still reaches the lowest rate any lender asks."""
    return maximum_rate - risk_premium(debt + taken, collateral_value, arrears, constants) >= lowest_ask


@njit
def fundable_amount(amount, debt, collateral_value, arrears, maximum_rate, lowest_ask, constants):
    """The most of `amount`, none up to all, the borrower can take at a rate it pays and a lender takes (a bisection on the edge)."""
    if amount <= 0.0 or not meets_lowest_ask(0.0, debt, collateral_value, arrears, maximum_rate, lowest_ask, constants):
        return 0.0
    if meets_lowest_ask(amount, debt, collateral_value, arrears, maximum_rate, lowest_ask, constants):
        return amount
    low, high = 0.0, amount
    for _step in range(int(constants[BISECTION_STEPS])):
        middle = (low + high) / 2.0
        if meets_lowest_ask(middle, debt, collateral_value, arrears, maximum_rate, lowest_ask, constants):
            low = middle
        else:
            high = middle
    return low
