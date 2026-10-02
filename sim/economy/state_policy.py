"""How a state budgets: what share of its pay goes to wages, how much cash it keeps, and the order
in which it covers a deficit. Data on the setup, so any actor with a treasury can be given one."""
from dataclasses import dataclass
from typing import Tuple

from sim.constants import declare

STATE_WAGE_SHARE = declare(
    "STATE_WAGE_SHARE", 0.5, kind="temporary_heuristic",
    unit="share of the state's yearly spending that bids for hours of labour, the rest buying goods",
    source=None, confidence="D",
    why="Stands in for budget lines (army pay, officials, supplies, works) that the engine does not yet "
        "supply; the split is a stated placeholder, not a measurement of any state's budget.")
STATE_CASH_SPEND_SHARE = declare(
    "STATE_CASH_SPEND_SHARE", 0.5, kind="temporary_heuristic",
    unit="share of the cash above the reserve target the state spends in a year",
    source=None, confidence="D",
    why="A treasury does not hold surplus coin for ever, but spends it down over some years; the pace is "
        "a placeholder for a budgeting rule the engine does not yet supply.")
STATE_RESERVE_YEARS_OF_REVENUE = declare(
    "STATE_RESERVE_YEARS_OF_REVENUE", 0.25, kind="temporary_heuristic",
    unit="years of the state's revenue it keeps in hand",
    source=None, confidence="D",
    why="A working reserve against a bad collection year; stands in for a treasury policy not yet modelled.")
STATE_FINANCING_ORDER = ("borrow", "issue", "debase")


@dataclass(frozen=True)
class StatePolicy:
    trades: Tuple[str, ...] = ()           # trades the state hires; empty: the unskilled trade
    financing_order: Tuple[str, ...] = STATE_FINANCING_ORDER   # tried in turn for a deficit
    real_spending_target: float = 0.0      # yearly spending in opening money, scaled by the price level; 0: spend what it has
    wage_share: float = STATE_WAGE_SHARE
    cash_spend_share: float = STATE_CASH_SPEND_SHARE
    reserve_years_of_revenue: float = STATE_RESERVE_YEARS_OF_REVENUE
