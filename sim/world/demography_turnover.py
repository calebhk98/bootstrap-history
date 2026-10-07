"""How fast a population's working-age band renews: people coming of working age and people leaving it.

Read from the population's age bands and the baseline mortality rates of `demography`, as shares of the
working-age band a year. Crisis mortality of the year is not included.
"""
from typing import Tuple

from .demography import (BASELINE_ANNUAL_MORTALITY_RATE_CHILD, BASELINE_ANNUAL_MORTALITY_RATE_WORKING_AGE,
                         CHILD_BAND_WIDTH_YEARS, WORKING_AGE_BAND_WIDTH_YEARS, Population)


def working_age_turnover(population: Population) -> Tuple[float, float]:
    """(entrants, leavers) a year as shares of the working-age band: surviving children aging into it,
    and deaths plus those aging out of it into the elderly band."""
    if population.working_age <= 0.0:
        return 0.0, 0.0
    survivors = population.children * (1.0 - min(1.0, BASELINE_ANNUAL_MORTALITY_RATE_CHILD))
    entrants = survivors / CHILD_BAND_WIDTH_YEARS / population.working_age
    leavers = (min(1.0, BASELINE_ANNUAL_MORTALITY_RATE_WORKING_AGE)
               + (1.0 - BASELINE_ANNUAL_MORTALITY_RATE_WORKING_AGE) / WORKING_AGE_BAND_WIDTH_YEARS)
    return entrants, leavers
