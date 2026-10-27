"""The arithmetic of what runs: industry depth, the revenue ceiling, the capability factor, institution upkeep and size. Plain values in, plain values out."""
from typing import Any, Mapping, Optional

from .constants import (CAPABILITY_FACTOR_CEILING_BONUS, CAPABILITY_FACTOR_HALF_SATURATION_REV_LABOUR_HOURS,
                        INSTITUTION_CEILING_POP_EXPONENT, INSTITUTION_FLOOR, LITERACY_GENERAL_FLOOR, RISK_SHARE_AT_FULL_DEPTH,
                        SCHOOL_CEILING_BASE_UNITS, WORKSHOP_CEILING_BASE_UNITS, YEARS_STAFF_TAKE_TO_MASTER)


def depth_risk_multiplier(depth: float) -> float:
	"""Share of a node's bare risk left once its industry is this deep."""
	return 1.0 - (1.0 - RISK_SHARE_AT_FULL_DEPTH) * depth


def mastery_worker_years(founding_worker_years: float) -> float:
	"""Worker-years that make an industry half established, for a concern of this staff."""
	return max(founding_worker_years, 1e-9) * YEARS_STAFF_TAKE_TO_MASTER


def industry_depth(experience: float, founding_worker_years: float) -> float:
	"""0 for a technique nobody has run, approaching 1 as it becomes established."""
	return experience / (experience + mastery_worker_years(founding_worker_years))


def industry_scale_ceiling(experience: float, founding_worker_years: float) -> float:
	"""The most founding sizes one concern can be run at: one, plus the experience in masters' worth of staff."""
	return 1.0 + experience / mastery_worker_years(founding_worker_years)


def saturated_revenue(gross: float, ceiling: float) -> float:
	"""The estimate of what the concerns nobody clears take in, squeezed under the market's ceiling without ever reaching it."""
	return gross / (1.0 + gross / max(1.0, ceiling))


def capability_factor(weight: float) -> float:
	"""How much better the methods held make the same pair of hands; `weight` is the tier-weighted revenue hours of what is built and not run."""
	return 1.0 + CAPABILITY_FACTOR_CEILING_BONUS * (weight / (weight + CAPABILITY_FACTOR_HALF_SATURATION_REV_LABOUR_HOURS))


def occupancy_scaled_upkeep(upkeep_amount: float, places: float, headcount: float) -> float:
	"""A capability institution's upkeep scaled by how full its places are: a fixed share however empty."""
	used = min(1.0, headcount / max(1.0, places))
	return upkeep_amount * (INSTITUTION_FLOOR + (1.0 - INSTITUTION_FLOOR) * used)


def institution_places(places_mechanic: Optional[Mapping[str, Any]], upkeep: float, upkeep_per_head: float) -> float:
	"""People one unit supports: the institution's own `institution_places` mechanic, else its upkeep at about a wage a head."""
	if places_mechanic is not None:
		return places_mechanic["flat"]
	return max(1.0, upkeep / upkeep_per_head)


def literacy_ceiling(population_scale: float, literacy: float, reference_literacy: float) -> float:
	"""Most units of a literacy-bound institution (a school) the people can fill."""
	floored = max(LITERACY_GENERAL_FLOOR, float(literacy))
	return max(1.0, SCHOOL_CEILING_BASE_UNITS * population_scale ** INSTITUTION_CEILING_POP_EXPONENT
	           * (floored / reference_literacy) ** INSTITUTION_CEILING_POP_EXPONENT)


def population_ceiling(population_scale: float) -> float:
	"""Most units of an institution bounded by craftsmen rather than the literate few (a workshop, a collegium)."""
	return max(1.0, WORKSHOP_CEILING_BASE_UNITS * population_scale ** INSTITUTION_CEILING_POP_EXPONENT)


def institution_cost_between(base_cost: float, have_units: float, add_units: float, convexity: float) -> float:
	"""Money to take an institution from `have_units` to `have_units + add_units`, where one unit costs `base_cost`."""
	def cumulative_cost(units: float) -> float:
		return units + convexity * 0.5 * max(0.0, units - 1.0) ** 2
	return base_cost * max(0.0, cumulative_cost(have_units + add_units) - cumulative_cost(have_units))
