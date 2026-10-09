"""Numerical choices of the sub-year step, and the exact-where-small binomial draw the step is built on."""
import math

from sim.constants import declare

STEP_DIVISOR = declare(
    "STEP_DIVISOR", 2.0, kind="temporary_heuristic", unit="steps per shortest stage sojourn", confidence="D",
    why="How many steps fit in the shortest mean stage sojourn of a pathogen. A numerical accuracy choice; "
        "the convergence test in sim/tests/test_disease_patch.py halves the step and checks the final size.")
STEP_MINIMUM_DAYS = declare(
    "STEP_MINIMUM_DAYS", 1.0, kind="temporary_heuristic", unit="days", confidence="D",
    why="Floor on the step so a pathogen with very short stages does not cost more than a daily step.")
STEP_MAXIMUM_DAYS = declare(
    "STEP_MAXIMUM_DAYS", 7.0, kind="temporary_heuristic", unit="days", confidence="D",
    why="Ceiling on the step so slow pathogens are still followed within the season.")
NORMAL_APPROXIMATION_MEAN = declare(
    "NORMAL_APPROXIMATION_MEAN", 25.0, kind="temporary_heuristic", unit="expected count", confidence="D",
    why="A binomial draw with a smaller expected count is exact (geometric skips); above it the draw uses a "
        "rounded normal, clamped to the source count. Keeps a large patch cheap.")


def binomial(rng, trials, probability):
    """Number of successes in `trials` independent chances of `probability`; never below 0 or above `trials`."""
    if trials <= 0 or probability <= 0.0:
        return 0
    if probability >= 1.0:
        return trials
    if probability > 0.5:
        return trials - binomial(rng, trials, 1.0 - probability)
    mean = trials * probability
    if mean < NORMAL_APPROXIMATION_MEAN:
        successes, position = 0, 0
        log_failure = math.log1p(-probability)
        while True:
            position += 1 + int(math.log(1.0 - rng.random()) / log_failure)
            if position > trials:
                return successes
            successes += 1
    draw = round(mean + math.sqrt(mean * (1.0 - probability)) * rng.gauss(0.0, 1.0))
    return max(0, min(trials, draw))


def chance_within(rate_per_day, days):
    """Probability that something with the given hazard per day happens during `days`."""
    return -math.expm1(-rate_per_day * days)
