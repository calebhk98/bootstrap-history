"""The immune state a pathogen that is already endemic leaves in a people, solved from the pathogen's own numbers.

At the endemic equilibrium a case replaces itself with one case, so the susceptible share of the people is the
reciprocal of the effective reproduction number (the pathogen's number at the place's crowding). A constant
force of infection per year makes people immune with age, so the susceptible share of an age band is the mean
of `exp(-force * age)` over the ages it spans; the force is the root that makes the people-weighted susceptible
share equal that reciprocal. Children are therefore mostly susceptible and adults mostly immune, which is what a
childhood disease looks like. Infected people follow from the incidence times each stage's length.
"""
import math

from sim.world import demography

from . import network

# age span of each band in years; the elderly band is given the working-age band's width (nobody is left in it
# for long, and its people are almost all immune whatever the width)
BAND_AGES = {"children": (0.0, demography.WORKING_AGE_LOWER_BOUND_YEARS),
             "working_age": (demography.WORKING_AGE_LOWER_BOUND_YEARS, demography.WORKING_AGE_UPPER_BOUND_YEARS),
             "elderly": (demography.WORKING_AGE_UPPER_BOUND_YEARS,
                         demography.WORKING_AGE_UPPER_BOUND_YEARS + demography.WORKING_AGE_BAND_WIDTH_YEARS)}
_BISECTION_STEPS = 60
_FORCE_CEILING_PER_YEAR = 50.0


def susceptible_share_of_band(force_per_year, ages):
    """Mean of exp(-force * age) over the ages a band spans: the share of it never infected."""
    start, end = ages
    if force_per_year <= 0.0:
        return 1.0
    return (math.exp(-force_per_year * start) - math.exp(-force_per_year * end)) / (force_per_year * (end - start))


def effective_reproduction_number(pathogen, crowding=1.0):
    """The pathogen's reproduction number among people at `crowding` times the density its transmissibility is stated at."""
    return network.reproduction_number(pathogen) * max(crowding, 0.0) ** pathogen.density_exponent


def endemic_force_per_year(pathogen, people_by_band, crowding=1.0):
    """The yearly force of infection that holds the susceptible share at the reciprocal of the effective
    reproduction number; 0.0 when the pathogen cannot sustain itself (that number at or below one)."""
    reproduction = effective_reproduction_number(pathogen, crowding)
    total = sum(people_by_band.values())
    if reproduction <= 1.0 or total <= 0.0:
        return 0.0

    def susceptible(force):
        return sum(people_by_band[band] * susceptible_share_of_band(force, BAND_AGES[band]) for band in people_by_band) / total

    low, high = 0.0, _FORCE_CEILING_PER_YEAR
    for _ in range(_BISECTION_STEPS):
        middle = 0.5 * (low + high)
        if susceptible(middle) > 1.0 / reproduction:
            low = middle
        else:
            high = middle
    return 0.5 * (low + high)


def endemic_counts(pathogen, people_by_band, crowding=1.0):
    """{band: {compartment: people}} an endemic setting holds: the immune, the infected in each stage (incidence
    times the stage's length) and the rest susceptible. Whole people; the band's total is kept."""
    force = endemic_force_per_year(pathogen, people_by_band, crowding)
    counts = {}
    for band, people in people_by_band.items():
        people = int(people)
        susceptible_share = susceptible_share_of_band(force, BAND_AGES[band])
        incidence_per_day = force * susceptible_share / 365.0
        band_counts = {name: 0 for name in network.compartment_ids(pathogen)}
        infected = 0
        for stage in pathogen.stages:
            per_substage = int(round(people * incidence_per_day * stage["mean_duration_in_days"] / stage["shape"]))
            for index in range(stage["shape"]):
                band_counts["%s.%d" % (stage["id"], index)] = per_substage
                infected += per_substage
        susceptible = min(people - infected, int(round(people * susceptible_share)))
        band_counts[network.SUSCEPTIBLE] = max(0, susceptible)
        band_counts[network.RECOVERED] = max(0, people - infected - band_counts[network.SUSCEPTIBLE])
        counts[band] = band_counts
    return counts
