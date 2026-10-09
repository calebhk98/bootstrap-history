"""One chain-binomial step of one patch, and advancing a patch by whole days.

Every person leaves a state with probability `1 - exp(-step / mean sojourn)`; the number leaving is a
binomial draw on the count in the source state, so counts stay whole and never go negative.
"""
from . import network
from .numerics import binomial, chance_within

_STEP_TOLERANCE = 1e-6


def step_patch(pathogen, patch, step_length_in_days=None):
    step = step_length_in_days or network.step_length_in_days(pathogen)
    counts, rng = patch.counts, patch.rng
    _background(patch, step)
    living = patch.living()
    if living <= 0:
        return
    stages = network.substages(pathogen)
    exits = [binomial(rng, counts[name], chance_within(rate, step)) for name, _, rate in stages]
    # A person present at the start of a step who leaves during it counts for half the step. With the
    # entry-at-step-end convention this makes the mean infectious time equal the stage's mean to second order.
    infectious_people = sum(infectiousness * (counts[name] - 0.5 * exit_count)
                            for (name, infectiousness, _), exit_count in zip(stages, exits))
    force = pathogen.transmissibility_per_day * infectious_people / living
    infections = binomial(rng, counts[network.SUSCEPTIBLE], chance_within(force, step))
    deaths = binomial(rng, exits[-1], pathogen.case_fatality)
    waned = 0
    if not pathogen.immunity_permanent and pathogen.immunity_duration_in_days:
        waned = binomial(rng, counts[network.RECOVERED], chance_within(1.0 / pathogen.immunity_duration_in_days, step))
    counts[network.SUSCEPTIBLE] += waned - infections
    counts[network.RECOVERED] += exits[-1] - deaths - waned
    previous_entry = infections
    for (name, _, _), left in zip(stages, exits):
        counts[name] += previous_entry - left
        previous_entry = left
    patch.deaths_from_disease += deaths


def _background(patch, step):
    counts, rng = patch.counts, patch.rng
    death_chance = chance_within(patch.background_deaths_per_person_per_year, step / 365.0)
    if death_chance > 0.0:
        for name in counts:
            died = binomial(rng, counts[name], death_chance)
            counts[name] -= died
            patch.deaths_background += died
    born = binomial(rng, patch.living(), chance_within(patch.births_per_person_per_year, step / 365.0))
    counts[network.SUSCEPTIBLE] += born
    patch.births += born


def advance_patch(pathogen, patch, days, step_length_in_days=None):
    """Run whole steps covering `days`; a fraction of a step carries over in the patch."""
    step = step_length_in_days or network.step_length_in_days(pathogen)
    patch.owed_days += days
    while patch.owed_days >= step * (1.0 - _STEP_TOLERANCE):
        step_patch(pathogen, patch, step)
        patch.owed_days -= step
    if abs(patch.owed_days) < step * _STEP_TOLERANCE:
        patch.owed_days = 0.0
