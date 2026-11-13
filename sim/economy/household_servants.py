"""Whole servants (Complaint 645): a servant works a year, not a share of one, so a household hires one whole or none.
The cohort is many households of equal size; each compares the cost of a whole servant's year with the worth of the
own hours that servant frees it, and cannot hire one it cannot pay for (a budget of None is unknown: no bound)."""
from typing import Optional

from sim.unit_conversions import HOURS_PER_PERSON_YEAR
from sim.world.climate_needs import PERSONS_PER_HOUSEHOLD

from .price_setting import choice_shares
from .households_work import WORK_CHOICE_INTENSITY


def households_in(people: float) -> float:
    """How many households a cohort's people make."""
    return max(0.0, people) / PERSONS_PER_HOUSEHOLD


def hired_hours_whole(needed_hours: float, households: float, own_hour_value: float, service_price_per_hour: float,
                      budget_per_household: Optional[float], servant_year_hours: float = HOURS_PER_PERSON_YEAR) -> float:
    """Hours of the work a cohort hires when each household hires a whole servant or none. A household's work is
    `needed_hours / households`; a servant's year costs `service_price_per_hour * servant_year_hours` whatever the work
    there is, and frees `own_hour_value` for each hour of work it takes off the household (at most the household's
    own). A household whose budget is below one servant's year hires none; of those that can pay, the share that
    hires is a logit on that cost against the worth of the hours freed (price_setting.choice_shares)."""
    if needed_hours <= 0.0 or households <= 0.0 or service_price_per_hour <= 0.0 or own_hour_value <= 0.0 or servant_year_hours <= 0.0:
        return 0.0
    cost = service_price_per_hour * servant_year_hours
    if budget_per_household is not None and budget_per_household < cost:
        return 0.0
    work_per_household = needed_hours / households
    freed = min(work_per_household, servant_year_hours)
    share = choice_shares([cost, own_hour_value * freed], WORK_CHOICE_INTENSITY)[0]
    return households * share * freed
