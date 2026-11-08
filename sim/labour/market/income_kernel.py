"""What a person expects a trade to pay in an area, over the grid (the kernels behind `expectations.expected_income`,
`income_at_graduation`, `idle_share_of`, `hours_arrived_since` and `graduates_coming`).

Everything is read by grid row (`area * trade_count + trade`) from the state's tables, the year's results (results_grid.py) and the
cohorts (cohort_book.py). A missing figure is NaN. Sums that the Python added with `sum` or `math.fsum` use `exact_sums`."""
import math
from typing import NamedTuple

import numpy as np

from sim.jit import njit

from .clearing_kernel import _clearing_target as target_for_demand
from .cohort_book import graduates_coming
from .exact_sums import exact_sum


class YearRates(NamedTuple):
    """What the year's rules read about the world."""
    hours: float                  # hours a worker sells in a year
    discount_rate: float          # per year
    career_years: float           # years
    value_of_life: float          # years of income a trade's yearly risk of death is priced at
    subsistence: np.ndarray       # per area: money a worker needs a year to keep his dependants at their floors; NaN: none stated
    risk: np.ndarray              # per trade: chance of dying at the work in a year
    training_years: np.ndarray    # per trade


@njit
def reservation_wage(rates, area, trade):
    """What an hour must pay: the outside option per hour plus the priced risk of the trade (`reservation.reservation_wage`)."""
    return rates.subsistence[area] / max(rates.hours, 1e-12) * (1.0 + max(0.0, rates.risk[trade]) * rates.value_of_life)


@njit
def vacant_hours(results, row):
    """Hours employers wanted that nobody supplied."""
    return max(0.0, results.hours_wanted[row] - results.hours_hired[row])


@njit
def hours_arrived(rates, results, people, present, area, trade, row):
    """`expectations.hours_arrived_since`: hours offered by workers who joined a trade needing no training since its clearing."""
    held = results.hours_held[row]
    if math.isnan(held) or rates.training_years[trade] > 0.0:
        return 0.0
    now = 0.0
    if present[row]:
        now = exact_sum(people[row], people.shape[1])
    arrived = now * rates.hours - held
    if arrived <= 0.0:
        return 0.0
    sold_share = results.hours_offered[row] / held if held > 0.0 else 1.0
    return arrived * min(1.0, sold_share)


@njit
def slid_wage(wage, reservation, offered, arrived, results, caps, hours, row, scratch_caps, scratch_hours):
    """The wage after hands that came since the clearing sell hours too: it slides down the bids (`target_for_demand`)."""
    first = results.demand_first[row]
    return min(wage, target_for_demand(reservation, offered + arrived, caps, hours, first, first + results.demand_count[row],
                                       scratch_caps, scratch_hours))


@njit
def expected_income(rates, results, caps, hours, people, present, area, trade, scratch_caps, scratch_hours):
    """`expectations.expected_income`: money a year one worker of the trade in the area can expect; NaN where the area states no
    subsistence."""
    floor = rates.subsistence[area]
    if math.isnan(floor):
        return np.nan
    row = area * rates.risk.shape[0] + trade
    if not results.cleared[row] or results.hours_hired[row] <= 0.0:
        if results.cleared[row] and vacant_hours(results, row) > 0.0:
            return max(floor, results.wage[row] * rates.hours)
        return floor
    wage = results.wage[row]
    offered = results.hours_offered[row]
    arrived = hours_arrived(rates, results, people, present, area, trade, row)
    if arrived > 0.0 and results.demand_count[row] > 0:
        wage = slid_wage(wage, reservation_wage(rates, area, trade), offered, arrived, results, caps, hours, row, scratch_caps, scratch_hours)
        offered += arrived
    share = min(1.0, results.hours_wanted[row] / offered) if offered > 0.0 else 1.0
    earned = max(floor, wage * rates.hours)
    return share * earned + (1.0 - share) * floor


@njit
def idle_share(results, row):
    """`expectations.idle_share_of`: the share of a trade's hands that sold no hours this year; one where no market was held."""
    if not results.cleared[row] or results.hours_offered[row] <= 0.0:
        return 1.0
    return min(1.0, max(0.0, 1.0 - results.hours_hired[row] / results.hours_offered[row]))


@njit
def income_at_graduation(rates, results, caps, hours, people, present, book, area, trade, chances, scratch_caps, scratch_hours):
    """`expectations.income_at_graduation`: what a trade is expected to pay once someone starting its training now has finished,
    keeping today's premium over the outside option only for the part of today's shortage the people already training will
    not fill; NaN where the area states no subsistence."""
    floor = rates.subsistence[area]
    row = area * rates.risk.shape[0] + trade
    if math.isnan(floor):
        return np.nan
    if not results.cleared[row] or results.hours_wanted[row] <= 0.0:
        return floor
    reservation = reservation_wage(rates, area, trade)
    arrived = hours_arrived(rates, results, people, present, area, trade, row)
    heading = results.wage[row] if math.isnan(results.target_wage[row]) else results.target_wage[row]
    if arrived > 0.0 and results.demand_count[row] > 0:
        heading = slid_wage(heading, reservation, results.hours_offered[row], arrived, results, caps, hours, row, scratch_caps, scratch_hours)
    rent = max(0.0, heading - reservation) * rates.hours
    now = floor + rent
    if rent <= 0.0:
        return floor
    supply_then = (results.hours_offered[row] + arrived) + graduates_coming(book, row, chances) * rates.hours
    finds_work = min(1.0, results.hours_wanted[row] / supply_then) if supply_then > 0.0 else 1.0
    shortage_now = results.hours_wanted[row] - results.hours_offered[row]
    if shortage_now <= 0.0:
        return floor + (now - floor) * finds_work
    shortage_then = results.hours_wanted[row] - supply_then
    remaining = max(0.0, min(1.0, shortage_then / shortage_now))
    return floor + (now - floor) * remaining
