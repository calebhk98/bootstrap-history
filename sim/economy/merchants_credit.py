"""A merchant borrows when a route's expected return beats the rate and its cash is what limits the cargo.

`credit_request` sizes the cargo its cash cannot buy on the routes it would otherwise run, within a share of
its own equity, and offers up to what those routes are expected to return. Staked capital counts what the
lenders put in, so repaying a loan lowers it with the cash and a write-off shows as profit; `stake` keeps
that account.
"""
import math
from typing import Mapping, Optional

from sim.constants import declare

from . import merchants
from .types import CurrencyId, LoanRequest

MERCHANT_LOAN_YEARS = declare(
    "MERCHANT_LOAN_YEARS", 4.0, kind="temporary_heuristic", unit="years",
    source=None, confidence="D",
    why="Cargo bought one year sells the next, after the first payment falls due, so a merchant's loan "
        "runs long enough that a year's installment and interest stay under the write-off point. Terms "
        "matched to the trading cycle need payments inside the year, which are not modelled.")
MERCHANT_LEVERAGE_LIMIT = declare(
    "MERCHANT_LEVERAGE_LIMIT", 0.25, kind="temporary_heuristic", unit="debt as a multiple of equity",
    source=None, confidence="D",
    why="A merchant owes no more than a share of its own stake. Lenders' own limits follow their view "
        "of the merchant's risk, which the premium on leverage prices only in part.")


def credit_request(merchant, view, carriage, area_map, cash: float, held_stock, specs, interest_rate: float,
                   debt: float, currency: CurrencyId) -> Optional[LoanRequest]:
    """A loan for the cargo that cash cannot buy, or None. The most it offers is the interest rate plus
    the average net return per unit of outlay on the routes the loan would fund."""
    equity = merchant.capital_base - debt
    limit = MERCHANT_LEVERAGE_LIMIT * equity - debt
    if limit <= 0.0:
        return None
    candidates = merchants._candidate_routes(merchant, view, carriage, area_map, held_stock, specs, interest_rate)
    remaining = max(0.0, cash)
    wanted, gain = 0.0, 0.0
    for rank, _good, _source, _destination, _price_here, outlay, room, _ceiling in candidates:
        paid_by_cash = min(remaining / outlay, room) if outlay > 0.0 else room
        remaining -= paid_by_cash * outlay
        extra = (room - paid_by_cash) * outlay
        if extra <= 0.0 or math.isnan(extra):
            continue
        extra = min(extra, limit - wanted)
        wanted += extra
        gain += extra * -rank
        if wanted >= limit:
            break
    if wanted <= 0.0:
        return None
    return LoanRequest(merchant.agent_id, currency, wanted, interest_rate + gain / wanted, MERCHANT_LOAN_YEARS,
                       wanted, "trade")


def stake(merchants_by_id: Mapping[str, object], change_by_agent: Mapping[str, float]) -> None:
    """Move each borrowing merchant's staked capital by what it borrowed (positive) or repaid or was freed
    of (negative)."""
    for agent, change in change_by_agent.items():
        merchant = merchants_by_id.get(agent)
        if merchant is not None and change != 0.0:
            merchant.capital_base = max(0.0, merchant.capital_base + change)
