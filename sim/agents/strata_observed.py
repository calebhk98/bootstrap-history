"""Strata read their income from the economy's household cohorts.

The cohorts of the whole home country, poorest per head first, form an income curve over the population.
Home strata are ranked by what their own trade or property would earn per head and each takes the slice of
the curve its members occupy: its income is what the cohorts in that slice earned, so the strata's
incomes add up to the cohorts' (scaled to the strata's headcount). No stratum is named: the rank comes
from the plan's trade or property share alone.
"""
from typing import Any, Dict, List, Sequence, Tuple

from . import stratum_year


def slice_income(curve: Sequence[Tuple[float, float]], first_person: float, last_person: float) -> float:
	"""The money earned by the people from the `first_person`-th to the `last_person`-th along the curve of
	(people, income) rows, each row's income spread evenly over its people."""
	total, passed = 0.0, 0.0
	for people, income in curve:
		start, end = max(first_person, passed), min(last_person, passed + people)
		if end > start:
			total += income * (end - start) / people
		passed += people
	return total


def rank_key(stratum: Any, world: Any) -> float:
	"""What the stratum's people would earn each, by the engine's own pay: how strata are ordered along the curve."""
	members = stratum.record.members
	if members <= 0.0:
		return 0.0
	earning = stratum_year.bonded_product(stratum, world) if stratum.is_bonded() else stratum_year.own_income(stratum, world)
	return earning / members


def observed_incomes(strata: List[Any], world: Any, curve: Sequence[Tuple[float, float]]) -> Dict[str, float]:
	"""Each stratum's name -> the income of its slice of the cohorts' curve, the strata laid end to end,
	poorest rank first, and their headcount scaled to the cohorts' people."""
	cohort_people = sum(people for people, _income in curve)
	members = sum(stratum.record.members for stratum in strata)
	if cohort_people <= 0.0 or members <= 0.0:
		return {}
	scale = cohort_people / members
	ordered = sorted(strata, key=lambda stratum: (rank_key(stratum, world), stratum.record.stratum))
	incomes, passed = {}, 0.0
	for stratum in ordered:
		reach = stratum.record.members * scale
		incomes[stratum.record.stratum] = slice_income(curve, passed, passed + reach) / scale
		passed += reach
	return incomes
