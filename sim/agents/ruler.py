"""A ruler's life and succession, for any state.

A ruler ages a year at a time and dies at the demography's baseline yearly mortality of his age band (child, working age,
elderly), scaled by the health the caller reads; an heir is born one childbearing age before, the midpoint of the fertile
band. At an accession the factions' backing decides how contested it is: the more evenly the two strongest are matched, the
likelier the challenger disputes it by arms (the engine settles that in `revolt.py`, at the seat). Nothing here knows a
dated accession; a ruler's death is a draw from his age.

    dispute_probability = 1 - (backing of strongest faction - backing of second) / total backing    (0 with fewer than two)
"""
import math
from statistics import NormalDist
from typing import Mapping, Optional, Tuple

from sim.constants import declare
from sim.world import demography

COMPETENCE_LOG_SPREAD = declare(
	"COMPETENCE_LOG_SPREAD", 0.4, kind="temporary_heuristic",
	unit="standard deviation of the log of competence", source=None, confidence="D",
	retire="Complaints/486: rulers and councils as actors with advisers, training and a record in office",
	why="How widely rulers differ in how well they run a state; competence is lognormal with a median of one. "
		"No source opened gives a spread; stands in for upbringing, advisers and experience.")
COMPETENCE_FLOOR = 0.05   # a ruler never has less than this, so the officials' take stays finite


def mortality_rate(age: float) -> float:
	"""Baseline yearly mortality of a person of this age: the demography's rate for the band the age falls in."""
	if age < demography.WORKING_AGE_LOWER_BOUND_YEARS:
		return demography.BASELINE_ANNUAL_MORTALITY_RATE_CHILD
	if age <= demography.WORKING_AGE_UPPER_BOUND_YEARS:
		return demography.BASELINE_ANNUAL_MORTALITY_RATE_WORKING_AGE
	return demography.BASELINE_ANNUAL_MORTALITY_RATE_ELDERLY


def death_probability(age: float, health_hazard: float = 1.0) -> float:
	"""Chance a ruler of this age dies within a year; `health_hazard` multiplies the baseline rate (1 is the band's own)."""
	return 1.0 - math.exp(-mortality_rate(age) * max(0.0, health_hazard))


def childbearing_age() -> float:
	"""Mean age at which a ruler's heir is born: the midpoint of the fertile band."""
	return 0.5 * (demography.WORKING_AGE_LOWER_BOUND_YEARS + demography.WORKING_AGE_UPPER_BOUND_YEARS)


def opening_age() -> float:
	"""A ruler found on the throne at the start of a game, with no record of his birth: the age of a parent."""
	return childbearing_age()


def heir_age(ruler_age: float) -> float:
	return max(0.0, ruler_age - childbearing_age())


def dies(age: float, health_hazard: float, draw: float) -> bool:
	return draw < death_probability(age, health_hazard)


def contenders(backing: Mapping[str, float]) -> Tuple[Optional[str], Optional[str]]:
	"""(strongest faction, runner-up) by backing, ties by id; None where there are fewer."""
	ranked = sorted((item for item in backing.items() if item[1] > 0.0), key=lambda item: (-item[1], item[0]))
	return (ranked[0][0] if ranked else None, ranked[1][0] if len(ranked) > 1 else None)


def dispute_probability(backing: Mapping[str, float]) -> float:
	leader, challenger = contenders(backing)
	if leader is None or challenger is None:
		return 0.0
	total = sum(value for value in backing.values() if value > 0.0)
	return 1.0 - (backing[leader] - backing[challenger]) / total


def draw_competence(draw: float, averaged: bool = False) -> float:
	"""A ruler's competence from a uniform `draw`: lognormal, median one. An averaged council is one whatever the draw."""
	if averaged:
		return 1.0
	z_score = NormalDist().inv_cdf(min(max(draw, 1e-6), 1.0 - 1e-6))
	return max(COMPETENCE_FLOOR, math.exp(COMPETENCE_LOG_SPREAD * z_score))


def reach_factor(competence: float) -> float:
	"""Share of its administrative reach a state keeps under a ruler of this competence (a strong ruler cannot reach beyond all)."""
	return max(0.0, min(1.0, competence))


def keep_factor(competence: float) -> float:
	"""What officials' take is multiplied by: a weak ruler is cheated more, a strong one less."""
	return 1.0 / max(COMPETENCE_FLOOR, competence)
