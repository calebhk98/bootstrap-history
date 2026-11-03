"""Baseline checks on a controlled run's yearly accounts (Complaint 554): physical feasibility (no good used beyond
what was made plus what was held) and the food eaten per head. Each returns the measured figures; the tests apply the bounds. Bounded dynamics are in settling.py. Changes nothing."""
from dataclasses import dataclass
from typing import Dict, List, Sequence

from sim.constants import declare

from .year_accounts import YearAccounts

FEASIBILITY_TOLERANCE = declare(
    "FEASIBILITY_TOLERANCE", 1e-6, kind="physical_constant", unit="share of the good's largest flow",
    why="float rounding in summing a year's flows; not a modelling allowance")


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


def food_eaten_over_need(accounts_by_year: Sequence[YearAccounts]) -> Dict[str, float]:
    """Each tile's food eaten per head over the hunger need's floor, in the last year."""
    return {tile.tile: tile.eaten_over_need for tile in accounts_by_year[-1].tiles} if accounts_by_year else {}
