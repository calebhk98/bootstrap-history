"""A pathogen's compartments and transitions as plain data, and what follows from them.

A pathogen is a chain of stages; a stage with `shape` k is k equal exponential substages (an Erlang
sojourn), so a bell-shaped duration needs no engine code. Compartments are `susceptible`, the substages in
order, and `recovered`.
"""
from .numerics import STEP_DIVISOR, STEP_MAXIMUM_DAYS, STEP_MINIMUM_DAYS

SUSCEPTIBLE = "susceptible"
RECOVERED = "recovered"


def substages(pathogen):
    """[(compartment_id, infectiousness, exit_rate_per_day)] for every substage, in order."""
    return [("%s.%d" % (stage["id"], index), stage["infectiousness"], stage["shape"] / stage["mean_duration_in_days"])
            for stage in pathogen.stages for index in range(stage["shape"])]


def compartment_ids(pathogen):
    return [SUSCEPTIBLE] + [name for name, _, _ in substages(pathogen)] + [RECOVERED]


def infected_ids(pathogen):
    return [name for name, _, _ in substages(pathogen)]


def reproduction_number(pathogen):
    """Secondary cases per case in a fully susceptible population: transmissibility times infectious days."""
    infectious_days = sum(stage["infectiousness"] * stage["mean_duration_in_days"] for stage in pathogen.stages)
    return pathogen.transmissibility_per_day * infectious_days


def herd_immunity_threshold(pathogen):
    """Immune share at which one case replaces itself with exactly one case."""
    return max(0.0, 1.0 - 1.0 / reproduction_number(pathogen))


def step_length_in_days(pathogen):
    shortest = min(1.0 / rate for _, _, rate in substages(pathogen))
    return max(STEP_MINIMUM_DAYS, min(STEP_MAXIMUM_DAYS, shortest / STEP_DIVISOR))
