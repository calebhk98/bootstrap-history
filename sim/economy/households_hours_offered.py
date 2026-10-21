"""How many of its working hours a household offers to the market (Complaint 473, 608).

An hour a household does not sell is not idle: it goes to its own plot, its household work and leisure. So the hours
offered are a choice against what an hour yields at home. On the plot, output rises with hours on fixed land to the
labour elasticity (world/land.py), so the next hour adds less the more hours are already there; the household keeps
hours on the plot until the next one adds no more than the wage. A household with no plot (no land held, or nothing
its land grows serves a need) has nothing to keep them for and offers all. The wage that holds the hours back is the
household's own outside option, not a typed survival figure. Hours left after the plot and household work are shared
between leisure and the market by a smooth preference (`leisure_hours_kept`), so the hours offered rise with the wage
without a step. Plain functions of built inputs.
"""
from typing import Optional, Tuple

from sim.constants import declare
from sim.world.shared_constants import LABOUR_OUTPUT_ELASTICITY

LEISURE_ELASTICITY = declare(
    "LEISURE_ELASTICITY", 2.0, kind="temporary_heuristic",
    unit="elasticity of the ratio of hours sold to leisure hours, with respect to the wage", source=None, confidence="D",
    retire="Complaints/673",
    why="A household splits the hours its plot and household work leave between leisure and sale; the more the wage "
        "pays against what its hours are worth at rest the more it sells. The figure only sets how smoothly the hours "
        "move with the wage, so that a small excess of hours moves the wage a little; no labour-supply study has been "
        "opened for it (673).")


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


def leisure_share(wage_per_hour: float, anchor_wage_per_hour: Optional[float], elasticity: float = LEISURE_ELASTICITY) -> float:
    """Share of free hours kept as leisure: one half at the anchor wage (the wage at which an hour at rest is worth
    as much as an hour sold), falling smoothly toward none as the wage rises and toward all as it falls. No anchor,
    or none above zero, means no leisure is valued."""
    if anchor_wage_per_hour is None or anchor_wage_per_hour <= 0.0:
        return 0.0
    if wage_per_hour <= 0.0:
        return 1.0
    return 1.0 / (1.0 + (wage_per_hour / anchor_wage_per_hour) ** elasticity)


def leisure_hours_kept(eligible_hours: float, wage_per_hour: float, anchor_wage_per_hour: Optional[float],
                       elasticity: float = LEISURE_ELASTICITY) -> float:
    """Hours of the `eligible_hours` a household keeps as leisure at this wage: the hours left after the plot and
    household work, less those its plot could still use (an hour it needs to grow its floors is not leisure)."""
    return max(0.0, eligible_hours) * leisure_share(wage_per_hour, anchor_wage_per_hour, elasticity)


def leisure_anchor_wage(eligible_hours: float, leisure_wanted: float, wage_per_hour: float,
                        elasticity: float = LEISURE_ELASTICITY) -> Optional[float]:
    """The anchor wage at which households keep exactly `leisure_wanted` of their `eligible_hours` as leisure at
    `wage_per_hour` (the inverse of `leisure_hours_kept`); None where none does: nothing wanted, or more wanted than
    there are hours to keep, which no leisure preference can bring about."""
    if eligible_hours <= 0.0 or leisure_wanted <= 0.0 or leisure_wanted >= eligible_hours or wage_per_hour <= 0.0:
        return None
    share = leisure_wanted / eligible_hours
    return wage_per_hour * (share / (1.0 - share)) ** (1.0 / elasticity)
