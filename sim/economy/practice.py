"""On-the-job learning of a producer's crew: the hours a run needs fall with the runs its crew has made.

The recipe's booked hours are the hours of a competent crew. A producer's record keeps the cumulative runs its crew has
made per trade (`Producer.practice`); `hours_multiplier` turns that into the share by which its hours exceed the
booked ones, on Wright's curve (`sim.labour.learning_curve`) down to the physical floor, so hours never go below the
recipe's. A trade with no entry is an established crew, at the floor: the opening's producers are existing workshops.

Follows Eurace@Unibi, which keeps skill with the workers and lets the firm's productivity follow the mean of its
workers' skills: Labour/Household_Employee_Functions.c Household_update_specific_skills closes a share of the gap
between a worker's specific skill and the firm's technology each month, never lowers it (no forgetting), and
Cons_Goods/Firm_Producer_Functions.c takes output per unit of capital as min(vintage productivity, specific skill).
Eurace's firm average is over its current employees (Labour/Firm_Employer_Functions.c, MEAN_SPECIFIC_SKILLS), so a
worker who leaves takes their skill and one who arrives brings theirs. Here workers are headcounts, not records, so the
crew's practice stays on the producer: runs added are the crew's, hires brought in by growth bring the pool's mean
practice and close the gap to the crew's at Eurace's rate, layoffs leave the stayers' practice as it was. A firm that
restarts takes the regional mean skill (Financial_Management/Firm_Financial_Management_Functions.c, after bankruptcy,
AVERAGE_S_SKILL_FROM_EUROSTAT): `entrant_units` takes the mean of the recipe's other producers.

Plain functions of numbers, plus `recipe_for`, which a producer's plan and run use in place of the booked recipe.
"""
import dataclasses
import math
from typing import Dict, Mapping, Sequence, Tuple

from sim.constants import declare
from sim.labour.api import SOURCE_TASK_FLOOR_FRACTION, learning_curve

SKILL_GAP_CLOSED_PER_YEAR = declare(
    "SKILL_GAP_CLOSED_PER_YEAR", 0.4991, kind="temporary_heuristic",
    unit="share of the gap between a hired hand's practice and the crew's closed in a year", source=None, confidence="C",
    retire="Complaints/644: per-worker skill held by the labour market, not a producer's crew average",
    why="Eurace@Unibi Household_update_specific_skills (Labour/Household_Employee_Functions.c) closes the gap monthly by "
        "1 - 0.5^(1/(20 + 0.25 (general_skill - 1) (4 - 20))), a half-life of 20 months at general skill 1 to 4 at "
        "skill 5 (formula switch skill_update_acc_to_formula = 1 and individual_learning = 0 in the shipped state "
        "run-trans/0_after_2k_transient.xml). Over twelve months the five levels close 0.340, 0.405, 0.500, 0.646 and "
        "0.875; weighted by the state's 148, 455, 676, 241 and 80 workers at each level the mean is 0.4991. The "
        "skill level mix of this simulation's workers is not modelled, so the state's mix stands in.")

_MULTIPLIER_STEP = 100.0        # multipliers are kept to a hundredth so a recipe has few practised copies
_practised: Dict[Tuple[int, Tuple[Tuple[str, float], ...]], tuple] = {}


def established_units() -> float:
    """Runs at which a crew is at the floor: the units of a trade with no entry in `Producer.practice`."""
    return learning_curve.cumulative_for_proficiency(1.0, SOURCE_TASK_FLOOR_FRACTION)


def hours_multiplier(units: float) -> float:
    """Hours a run takes over the booked hours, from the first attempt's (the floor's inverse) down to one."""
    return learning_curve.unit_time_ratio(units, SOURCE_TASK_FLOOR_FRACTION) / SOURCE_TASK_FLOOR_FRACTION


def units_after_year(units: float, runs: float, hired_share: float, pool_units: float,
                     closing: float = SKILL_GAP_CLOSED_PER_YEAR) -> float:
    """The crew's cumulative runs after a year of `runs`. Hands hired in (`hired_share` of the crew) come with
    `pool_units` and close `closing` of the gap up to the crew's; practice is never lowered."""
    share = max(0.0, min(1.0, hired_share))
    gap = max(0.0, units - pool_units)
    hired_units = pool_units + closing * gap
    mixed = (1.0 - share) * units + share * hired_units
    return mixed + max(0.0, runs)


def entrant_units(others_units: Sequence[float]) -> float:
    """A new producer's start: the mean practice of the recipe's other producers; a first attempt when it has none."""
    if not others_units:
        return 1.0
    return math.fsum(others_units) / len(others_units)


def hired_share(runs_before: float, runs_now: float) -> float:
    """Share of this year's crew that was not there last year: growth is hired, a fall is laid off (stayers keep
    their practice). Zero before a first year."""
    if runs_before < 0.0 or runs_now <= 0.0:
        return 0.0
    return max(0.0, 1.0 - runs_before / runs_now)


def recipe_for(recipe, practice: Mapping[str, float]):
    """The recipe with each trade's booked hours times that trade's hours multiplier; the booked recipe itself when
    every multiplier is one."""
    if not practice:
        return recipe
    multipliers = tuple((trade, round(hours_multiplier(practice[trade]) * _MULTIPLIER_STEP) / _MULTIPLIER_STEP)
                        for trade in sorted(recipe.labour_hours) if trade in practice)
    if all(multiplier <= 1.0 for _trade, multiplier in multipliers):
        return recipe
    key = (id(recipe), multipliers)
    kept = _practised.get(key)
    if kept is None or kept[0] is not recipe:
        scaled = dict(recipe.labour_hours)
        for trade, multiplier in multipliers:
            scaled[trade] = scaled[trade] * max(1.0, multiplier)
        kept = _practised[key] = (recipe, dataclasses.replace(recipe, labour_hours=scaled))
    return kept[1]


def units_of(crew_runs: Mapping[str, float], trade: str) -> float:
    return crew_runs.get(trade, established_units())


def pool_units(producers_of_recipe: Sequence[Mapping[str, float]], trade: str) -> float:
    """Mean practice at `trade` over the recipe's producers (an established crew counts at the floor)."""
    return entrant_units([units_of(crew_runs, trade) for crew_runs in producers_of_recipe]) if producers_of_recipe else 1.0


def entrant_crew_runs(recipe, peers: Sequence[Mapping[str, float]]) -> Dict[str, float]:
    """A new producer's crew_runs: the peers' mean per trade, left out where it is already at the floor."""
    start = {trade: pool_units(peers, trade) for trade in sorted(recipe.labour_hours)}
    return {trade: units for trade, units in start.items() if hours_multiplier(units) > 1.0}


def crew_runs_after_year(crew_runs: Mapping[str, float], runs_per_workshop: float, hired: float,
                         pool: Mapping[str, float]) -> Dict[str, float]:
    """Each trade the crew is still learning gains the year's runs; those at the floor are dropped, as established."""
    grown = {trade: units_after_year(units, runs_per_workshop, hired, pool.get(trade, units))
             for trade, units in sorted(crew_runs.items())}
    return {trade: units for trade, units in grown.items() if hours_multiplier(units) > 1.0}
