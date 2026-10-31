"""How much of a request a lender-priced premium lets a borrower take: the largest amount at which its ceiling (its
maximum rate less the premium on its debt after the loan) still meets the lowest rate any lender asks."""
from typing import Callable

BISECTION_STEPS = 60      # a numerical bound on the search for the largest amount, not a model figure

COLLATERAL_BOUND = "collateral_bound"      # the cause kept on a request funded for less than it asked


def fundable_amount(amount: float, existing_debt: float, collateral_value: float, arrears: float, maximum_rate: float,
                    lowest_ask: float, premium: Callable[[float, float, float], float]) -> float:
    """The most of `amount`, from none up to all of it, that the borrower can take at a rate it will pay and a lender
    will take. `premium(debt_after, collateral_value, arrears)` rises with the debt, so the search narrows on the edge."""
    def meets(taken: float) -> bool:
        return maximum_rate - premium(existing_debt + taken, collateral_value, arrears) >= lowest_ask
    if amount <= 0.0 or not meets(0.0):
        return 0.0
    if meets(amount):
        return amount
    low, high = 0.0, amount
    for _step in range(BISECTION_STEPS):
        middle = (low + high) / 2.0
        if meets(middle):
            low = middle
        else:
            high = middle
    return low
