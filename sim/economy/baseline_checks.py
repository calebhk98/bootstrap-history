"""Baseline checks on a controlled run's yearly accounts (Complaint 554): physical feasibility (no good used beyond
what was made plus what was held) and reproduction (stocks, food and the money stock can be kept up). Each returns
the measured figures; the tests apply the bounds. Bounded dynamics are in settling.py. Changes nothing."""
import math
from dataclasses import dataclass
from typing import Dict, List, Mapping, Sequence

from sim.constants import declare

from .year_accounts import YearAccounts

FEASIBILITY_TOLERANCE = declare(
    "FEASIBILITY_TOLERANCE", 1e-6, kind="physical_constant", unit="share of the good's largest flow",
    why="float rounding in summing a year's flows; not a modelling allowance")
MAX_STOCK_DEPLETION = declare(
    "MAX_STOCK_DEPLETION", 0.2, kind="temporary_heuristic", unit="share of a good's stock lost over the window",
    why="a run that can keep going does not eat through the stocks it holds; unsourced", retire="Complaints/473")
MIN_MONEY_REPLACEMENT = declare(
    "MIN_MONEY_REPLACEMENT", 0.9, kind="temporary_heuristic", unit="share of the coin worn that the mint replaced",
    why="a money stock that lasts is replaced as it wears; unsourced", retire="Complaints/473")


@dataclass(frozen=True)
class Overdraw:
    year: int
    good: str
    kind: str          # "uses_exceed_supply", "unexplained_stock_change" or "negative_stock"
    amount: float      # units, positive


def _scale(account) -> float:
    return max(account.production, account.intermediate_use, account.final_consumption, account.stock_at_start, 1.0)


def feasibility(accounts_by_year: Sequence[YearAccounts]) -> List[Overdraw]:
    """Every year and good where more was used than was made, brought in and held, where the flows leave part of
    the stock change unexplained, or where a stock went below nothing. Empty when the run is physically feasible."""
    found = []
    for accounts in accounts_by_year:
        for good, account in accounts.goods.items():
            tolerance = FEASIBILITY_TOLERANCE * _scale(account)
            used = (account.intermediate_use + account.final_consumption + account.state_use + account.investment
                    + account.other_use + account.spoilage)
            supply = account.production + account.other_net_inflow + account.stock_at_start
            if used - supply > tolerance:
                found.append(Overdraw(accounts.year, good, "uses_exceed_supply", used - supply))
            if abs(account.residual()) > tolerance:
                found.append(Overdraw(accounts.year, good, "unexplained_stock_change", abs(account.residual())))
            if account.stock_at_start + account.stock_change < -tolerance:
                found.append(Overdraw(accounts.year, good, "negative_stock",
                                      -(account.stock_at_start + account.stock_change)))
    return found


def stock_depletion(accounts_by_year: Sequence[YearAccounts]) -> Dict[str, float]:
    """Share of each good's stock at the start of the first year that is gone by the end of the last (zero when it
    grew or the good was not held)."""
    if not accounts_by_year:
        return {}
    first, last = accounts_by_year[0], accounts_by_year[-1]
    shares = {}
    for good, account in first.goods.items():
        if account.stock_at_start <= 0.0:
            continue
        final = last.goods[good].stock_at_start + last.goods[good].stock_change if good in last.goods else 0.0
        shares[good] = max(0.0, 1.0 - final / account.stock_at_start)
    return shares


def food_eaten_over_need(accounts_by_year: Sequence[YearAccounts]) -> Dict[str, float]:
    """Each tile's food eaten per head over the hunger need's floor, in the last year."""
    return {tile.tile: tile.eaten_over_need for tile in accounts_by_year[-1].tiles} if accounts_by_year else {}


def money_replacement(rows: Sequence[Mapping[str, float]], window_years: int) -> float:
    """Coin the mint struck (net of melting) over the coin worn away, across the last `window_years` rows of
    `economy_port_trace.spin_up_trace`; one when the mint exactly replaces wear."""
    recent = rows[-window_years:]
    wear = math.fsum(row["wear"] for row in recent)
    return math.fsum(row["struck"] for row in recent) / wear if wear > 0.0 else math.inf
