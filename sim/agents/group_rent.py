"""Landholders' income from the land market: the rent producers paid on the land they let, shared among the
propertied bodies of people, in place of their property share of the society's output."""
from typing import Any, Dict, List, Optional

from .stratum_year import PROPERTY, income_parts


def rent_total(world: Any) -> float:
	"""The rent producers paid last year on every tile where land was let; zero where none was let."""
	return sum(world.land_rent_paid_by_tile().values())


def rent_of(stratum: Any, holders: List[Any], world: Any) -> Optional[float]:
	"""The rent that went to this stratum: the land market's rent shared among the propertied strata in
	proportion to their property share (TEMPORARY HEURISTIC, CLAUDE.md 4.4: the agent economy keeps rent with
	its household cohorts, not with the strata, until ownership of tiles is recorded). None where no land was let."""
	total = rent_total(world)
	weight = float(stratum.record.plan.get("property_share") or 0.0)
	weights = sum(float(holder.record.plan.get("property_share") or 0.0) for holder in holders)
	if total <= 0.0 or weight <= 0.0 or weights <= 0.0:
		return None
	return total * weight / weights


def grievance_parts(stratum: Any, holders: List[Any], world: Any) -> Dict[str, float]:
	"""What the stratum earns by wages and by property, with its property income read from the land market's
	rent where land was let (else its share of the society's output)."""
	parts = income_parts(stratum, world)
	if PROPERTY in parts:
		rent = rent_of(stratum, holders, world)
		if rent is not None:
			parts[PROPERTY] = rent
	return parts
