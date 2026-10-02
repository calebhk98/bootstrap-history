"""How a state pays for spending it cannot meet from revenue and cash: borrow in the credit market,
then print (fiat), or strike the same metal into more coin (a struck coin, debased). The order is the
policy's; which methods are open follows from the currency's regime, never from who the state is."""
from typing import Dict, Tuple

from sim.constants import declare

from . import currency
from .types import LoanRequest

DEBT_LIMIT_YEARS_OF_REVENUE = declare(
    "DEBT_LIMIT_YEARS_OF_REVENUE", 3.0, kind="temporary_heuristic",
    unit="years of revenue a state may owe before it stops asking lenders",
    source=None, confidence="D",
    why="Lenders ration a borrower by its ability to service, which the credit market prices through the "
        "collateral it is shown; until revenue-backed credit is modelled this caps what the state asks for.")
STATE_LOAN_YEARS = declare(
    "STATE_LOAN_YEARS", 5.0, kind="temporary_heuristic", unit="years",
    source=None, confidence="D",
    why="Term of a state's borrowing; stands in for a bond market with its own maturities.")
STATE_BORROWING_RATE_CEILING_MULTIPLE = declare(
    "STATE_BORROWING_RATE_CEILING_MULTIPLE", 3.0, kind="temporary_heuristic",
    unit="multiple of the market rate the state will pay",
    source=None, confidence="D",
    why="A state wants the money more than a firm does, but not at any price; placeholder for its "
        "alternatives (taxing harder, spending less).")
STATE_COLLATERAL_YEARS_OF_REVENUE = declare(
    "STATE_COLLATERAL_YEARS_OF_REVENUE", 5.0, kind="temporary_heuristic",
    unit="years of revenue shown to lenders as the state's security",
    source=None, confidence="D",
    why="The state pledges its future taxes; how many years lenders credit is a placeholder for a "
        "credit-rating model not yet built.")


def finance_deficit(policy, record, view, setup, deficit: float, revenue: float) -> Tuple[float, float, Dict[str, float]]:
    """Cover `deficit` by the policy's order. Returns (money in hand now, money expected from lenders
    later this year, what each method supplied). Issuing and debasing book money at once; a loan
    request joins the credit market's queue and pays out when it clears."""
    money = setup.currency_id
    state = setup.state_agent
    remaining = deficit
    in_hand = expected = 0.0
    supplied: Dict[str, float] = {}
    for method in policy.financing_order:
        if remaining <= 0.0:
            break
        if method == "borrow":
            owed = sum(loan.principal for loan in record.loans if loan.borrower == state)
            headroom = max(0.0, DEBT_LIMIT_YEARS_OF_REVENUE * revenue - owed)
            amount = min(remaining, headroom)
            if amount <= 0.0:
                continue
            rate = max(view.interest_rate(money), 1e-9)
            record.loan_requests.append(LoanRequest(
                state, money, amount, rate * STATE_BORROWING_RATE_CEILING_MULTIPLE, STATE_LOAN_YEARS,
                revenue * STATE_COLLATERAL_YEARS_OF_REVENUE, "state deficit"))
            expected += amount
        elif method == "issue" and record.currency.regime == "fiat":
            record.book.transfer_many(currency.issue(record.currency, remaining, "state deficit"))
            amount = remaining
            in_hand += amount
        elif method == "debase" and record.currency.regime == "struck_coin":
            amount = remaining
            supply = record.book.money_supply(money)
            record.book.transfer_many(currency.issue(record.currency, amount, "state deficit"))
            # the same metal now backs more coin: each unit holds its share of it
            record.currency = currency.debase(record.currency,
                                              record.currency.backing_per_unit * supply / (supply + amount))
            in_hand += amount
        else:
            continue
        supplied[method] = amount
        remaining -= amount
    return in_hand, expected, supplied
