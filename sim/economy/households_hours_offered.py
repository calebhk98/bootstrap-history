"""How many of its working hours a household offers to the market (Complaint 473, 608).

An hour a household does not sell is not idle: it goes to its own plot and its household work (no leisure: Eurace@Unibi
households have no hours decision, Labour/Household_Employee_Functions.c). So the hours offered are a choice against
what an hour yields at home. On the plot, output rises with hours on fixed land to the
labour elasticity (world/land.py), so the next hour adds less the more hours are already there; the household keeps
hours on the plot until the next one adds no more than the wage. A household with no plot (no land held, or nothing
its land grows serves a need) has nothing to keep them for and offers all. The wage that holds the hours back is the
household's own outside option, not a typed survival figure. Every hour left after the plot and household work is
offered. Plain functions of built inputs.
"""
from typing import Tuple

from sim.world.shared_constants import LABOUR_OUTPUT_ELASTICITY


def plot_hours_kept(hours_available: float, wage_per_hour: float, plot_return_per_hour: float,
                    plot_hours_usable: float, elasticity: float = LABOUR_OUTPUT_ELASTICITY) -> float:
    """Hours a household keeps for its plot rather than sell.

    `plot_return_per_hour` is what the next hour adds on the plot with the whole of `hours_available` on it (money at
    the prices of what it grows, labour_ask_floor.plot_return_per_hour); with `hours` on it the next hour adds that
    times (hours_available / hours) to the power (1 - elasticity). It keeps hours down to where this equals the wage,
    never more than the plot can take (`plot_hours_usable`: the floors the plot grows, on the land held). A wage that
    is not positive keeps every usable hour; a plot that adds nothing keeps none."""
    if hours_available <= 0.0 or plot_hours_usable <= 0.0 or plot_return_per_hour <= 0.0:
        return 0.0
    usable = min(hours_available, plot_hours_usable)
    if wage_per_hour <= 0.0:
        return usable
    return min(usable, hours_available * (plot_return_per_hour / wage_per_hour) ** (1.0 / (1.0 - elasticity)))


def hours_offered(hours_available: float, hours_kept_for_home: float) -> float:
    """What a household offers: its working hours less those it keeps for its plot and its household work."""
    return max(0.0, hours_available - max(0.0, hours_kept_for_home))


def wage_that_offers(hours_available: float, hours_offered_wanted: float, plot_return_per_hour: float,
                     plot_hours_usable: float, elasticity: float = LABOUR_OUTPUT_ELASTICITY) -> float:
    """The wage per hour at which a household offers `hours_offered_wanted` (the inverse of `plot_hours_kept`); None
    where no wage gives it: the household would keep more than its plot can take, or keep nothing (only an
    unbounded wage does that)."""
    kept = hours_available - hours_offered_wanted
    if kept <= 0.0 or kept > plot_hours_usable or plot_return_per_hour <= 0.0:
        return None
    return plot_return_per_hour * (hours_available / kept) ** (1.0 - elasticity)


def unsold_hours_to_home(hours_offered_to_market: float, hours_sold: float) -> Tuple[float, float]:
    """(hours sold, hours that go back to own production the same year): an hour no employer took is worked at home,
    not lost."""
    sold = min(max(0.0, hours_sold), max(0.0, hours_offered_to_market))
    return sold, max(0.0, hours_offered_to_market) - sold
