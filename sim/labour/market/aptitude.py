"""Ability bands: why a surgeon is paid well although anyone may try to become one.

Each area's people are split into equal-share bands of one aptitude distribution (a standard normal,
measured in standard deviations). A trade's `difficulty` is the ability at which half of those who start
its training finish it; the chance of finishing is logistic in ability minus difficulty. Few people in
the low bands finish a hard trade, so its eligible pool stays small and its wage keeps a premium however
much it pays (a Roy / Sattinger scarcity rent), with no premium written down anywhere.
"""
import functools
import math
from statistics import NormalDist
from typing import List, Mapping, Optional, Sequence

from sim.constants import declare

ABILITY_BAND_COUNT = declare(
    "ABILITY_BAND_COUNT", 5, kind="temporary_heuristic", unit="bands", source=None, confidence="D",
    why="How finely the aptitude distribution is cut. Every count in the labour core is per band, so the "
        "core's cost grows with it; five is the fewest that still separates the top fifth (who can finish "
        "the hardest trades) from the middle.")

COMPLETION_SPREAD = declare(
    "COMPLETION_SPREAD", 0.5, kind="temporary_heuristic",
    unit="ability standard deviations per e-fold of the odds of finishing", source=None, confidence="D",
    why="How sharply the chance of finishing a training falls off below the trade's difficulty. Smaller is a "
        "harder cliff. Apprenticeship completion was far from certain even for the able (indentures were "
        "often left unfinished), so it is not a threshold; the width is not fitted.")

DIFFICULTY_AT_NO_TRAINING = declare(
    "DIFFICULTY_AT_NO_TRAINING", -3.0, kind="temporary_heuristic", unit="ability standard deviations",
    source=None, confidence="D",
    why="Difficulty of a trade that states none and needs no training: nearly everyone can do it. Used only "
        "until the trade registry carries a difficulty per trade.")

DIFFICULTY_PER_TRAINING_YEAR = declare(
    "DIFFICULTY_PER_TRAINING_YEAR", 0.45, kind="temporary_heuristic",
    unit="ability standard deviations per year of training", source=None, confidence="D",
    why="Stand-in for a trade's difficulty when the registry states none: longer trainings are taken as "
        "harder to finish. Training length and difficulty are different things (a long apprenticeship can "
        "be custom, not difficulty), so this goes when the data carries a difficulty.")


@functools.lru_cache(maxsize=None)
def _bands(count: int) -> tuple:
    distribution = NormalDist()
    return tuple(distribution.inv_cdf((index + 0.5) / count) for index in range(count))


def band_count() -> int:
    return int(ABILITY_BAND_COUNT)


def band_abilities() -> List[float]:
    """Each band's ability: the middle quantile of its equal share of the population."""
    return list(_bands(band_count()))


def split_evenly(people: float) -> List[float]:
    """People spread across the bands as the population is (equal shares)."""
    count = band_count()
    return [people / count] * count


def empty_bands() -> List[float]:
    return [0.0] * band_count()


def difficulty_from(training_years: float, stated: Optional[float] = None) -> float:
    """A trade's difficulty: as the data states it, else the training-years stand-in."""
    if stated is not None:
        return float(stated)
    return DIFFICULTY_AT_NO_TRAINING + DIFFICULTY_PER_TRAINING_YEAR * max(0.0, float(training_years))


def completion_chance(ability: float, difficulty: float, bonus: float = 0.0) -> float:
    """Chance that someone of this ability finishes a training of this difficulty."""
    exponent = -(ability + bonus - difficulty) / COMPLETION_SPREAD
    if exponent > 700.0:
        return 0.0
    return 1.0 / (1.0 + math.exp(exponent))


def completion_by_band(difficulty: float, bonus: float = 0.0) -> List[float]:
    return [completion_chance(ability, difficulty, bonus) for ability in band_abilities()]


def add_bands(into: List[float], extra: Sequence[float], scale: float = 1.0) -> None:
    for index, value in enumerate(extra):
        into[index] += value * scale


def band_total(bands: Sequence[float]) -> float:
    return math.fsum(bands)


def bands_of(mapping: Mapping, key) -> List[float]:
    """The band list stored under `key`, created empty if absent."""
    if key not in mapping:
        mapping[key] = empty_bands()
    return mapping[key]
