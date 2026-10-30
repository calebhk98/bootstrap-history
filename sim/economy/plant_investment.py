"""How much plant a producer invests in at a year's end, a port of Eurace@Unibi's investment rule.

Eurace (Cons_Goods/Firm_Producer_Functions.c, Firm_calc_input_demands) depreciates the capital stock, takes the output
the stock left can make (`feasible_output`), and when the planned output is above it demands capital for the
difference, no more than `INV_INERTIA` times the units depreciated that period. With the output planned at or below
what the stock can make nothing is bought and the stock is left to wear. Here the producer's plant is its
`capacity_runs`, the wear is the service life the recipe's plant has (`plant_life_years`), and the plan is the runs
`producers.runs_for_stock` calls for. The invested runs are split into the wear replaced, which the economy's year pays
from the producer's own earnings (`Economy._rebuild_worn_plant`), and the growth beyond it, which is asked of the credit
market (`producers_close._expansion`).
"""
from typing import Tuple

from sim.constants import declare

INVESTMENT_INERTIA = declare(
    "INVESTMENT_INERTIA", 2.0, kind="temporary_heuristic",
    unit="years of wear a producer's yearly plant investment can reach", source=None, confidence="D",
    retire="Complaints/473-the-agent-economy-spin-up-never-settles-so-the-opening-is-a-point-on-a-cycle.md",
    why="Eurace@Unibi's INV_INERTIA (Cons_Goods/Firm_Producer_Functions.c, Firm_calc_input_demands) caps capital demand at "
        "this multiple of the units depreciated; the C reads it from the initial data, and the value 2 is the one its "
        "unit tests (Cons_Goods/unittests/unittest_Firm.c) set. Builders, a lender to find and the time to build bound "
        "how fast plant is added; those are not modelled, so a multiple of the wear stands for them.")


def investment_runs(planned_runs: float, standing_runs: float, wear_runs: float, inertia: float = INVESTMENT_INERTIA) -> float:
    """The runs of plant to invest in: the gap between the runs planned and the capacity left after wear, no more than
    `inertia` times the year's wear (Eurace Firm_calc_input_demands: DEMAND_CAPITAL_STOCK against
    INV_INERTIA * TOTAL_CAPITAL_DEPRECIATION_UNITS). Zero when the plant left covers the plan."""
    gap = planned_runs - standing_runs
    if gap <= 0.0:
        return 0.0
    return min(gap, inertia * max(0.0, wear_runs))


def split(investment: float, wear_runs: float) -> Tuple[float, float]:
    """(wear replaced, growth added): the wear comes first, from earnings; only what is added beyond it is borrowed for."""
    replacement = min(investment, max(0.0, wear_runs))
    return replacement, investment - replacement
