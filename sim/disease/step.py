"""One chain-binomial step of one patch, and advancing a patch by whole days.

Every person leaves a state with probability `1 - exp(-step / mean sojourn)`; the number leaving is a
binomial draw on the count in the source state, so counts stay whole and never go negative.
"""
from . import network
from .numerics import binomial, chance_within

_STEP_TOLERANCE = 1e-6


def step_patch(pathogen, patch, step_length_in_days=None):
    step_groups(pathogen, {"all": patch}, step_length_in_days)


def care_collapse_multiplier(patches, care_collapse):
    """Multiplier on case fatality from the share of the caregiving bands that is ill right now.
    `care_collapse` is `(caregiver band keys, sensitivity)` or None; the multiplier is one plus the
    sensitivity times the ill share, so a lone case changes nothing and a nation in bed is deadliest."""
    if not care_collapse:
        return 1.0
    keys, sensitivity = care_collapse
    caregivers = [patches[key] for key in keys if key in patches]
    living = sum(patch.living() for patch in caregivers)
    if living <= 0:
        return 1.0
    return 1.0 + sensitivity * sum(patch.infected_now() for patch in caregivers) / living


def step_groups(pathogen, patches, step_length_in_days=None, fatality_scale=None, transmission_scale=1.0,
                care_collapse=None):
    """One step of several patches (age bands) that mix as one: the force of infection pools their
    infectious people and their living, and each patch draws its own fatality (the pathogen's, times that
    patch's entry in `fatality_scale`, times the care-collapse multiplier of the step). Deaths leave the counts, so they leave the contact denominator."""
    step = step_length_in_days or network.step_length_in_days(pathogen)
    stages = network.substages(pathogen)
    for patch in patches.values():
        _background(patch, step)
    living = sum(patch.living() for patch in patches.values())
    if living <= 0:
        return
    exits = {key: [binomial(patch.rng, patch.counts[name], chance_within(rate, step)) for name, _, rate in stages]
             for key, patch in patches.items()}
    # A person present at the start of a step who leaves during it counts for half the step. With the
    # entry-at-step-end convention this makes the mean infectious time equal the stage's mean to second order.
    infectious_people = sum(
        infectiousness * (patch.counts[name] - 0.5 * exit_count)
        for key, patch in patches.items()
        for (name, infectiousness, _), exit_count in zip(stages, exits[key]))
    care = care_collapse_multiplier(patches, care_collapse)
    force = pathogen.transmissibility_per_day * transmission_scale * infectious_people / living
    for key, patch in patches.items():
        _advance_one(pathogen, patch, stages, exits[key], force, step,
                     fatality=min(1.0, pathogen.case_fatality * (fatality_scale or {}).get(key, 1.0) * care))


def _advance_one(pathogen, patch, stages, exits, force, step, fatality):
    counts, rng = patch.counts, patch.rng
    infections = binomial(rng, counts[network.SUSCEPTIBLE], chance_within(force, step))
    deaths = binomial(rng, exits[-1], fatality)
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


def advance_groups(pathogen, patches, days, step_length_in_days=None, fatality_scale=None, transmission_scale=1.0,
                   care_collapse=None):
    """Run whole steps covering `days` over patches that mix as one; the fraction of a step left over is
    carried in the first patch's `owed_days`."""
    step = step_length_in_days or network.step_length_in_days(pathogen)
    anchor = next(iter(patches.values()))
    anchor.owed_days += days
    while anchor.owed_days >= step * (1.0 - _STEP_TOLERANCE):
        step_groups(pathogen, patches, step, fatality_scale, transmission_scale, care_collapse)
        anchor.owed_days -= step
    if abs(anchor.owed_days) < step * _STEP_TOLERANCE:
        anchor.owed_days = 0.0


def wane_idle(pathogen, patch, days):
    """Immunity lost over `days` in a patch with nobody infected (no step needed)."""
    if pathogen.immunity_permanent or not pathogen.immunity_duration_in_days:
        return
    waned = binomial(patch.rng, patch.counts[network.RECOVERED], chance_within(1.0 / pathogen.immunity_duration_in_days, days))
    patch.counts[network.RECOVERED] -= waned
    patch.counts[network.SUSCEPTIBLE] += waned


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
