"""Landholders' income from the land market: the rent producers paid on the land they let, as each body of people
received it, in place of their property share of the society's output."""
from typing import Any, Dict, List, Optional

from .stratum_year import PROPERTY, income_parts


def rent_total(world: Any) -> float:
	"""The rent producers paid last year on every tile where land was let; zero where none was let."""
	return sum(world.land_rent_paid_by_tile().values())


def rent_of(stratum: Any, holders: List[Any], world: Any) -> Optional[float]:
	"""The rent that went to this stratum: its slice of the rent the household cohorts received by what each owns
	(`world.land_rent_owners`, the same owners a land tax is drawn from). None where no land was let."""
	if rent_total(world) <= 0.0:
		return None
	received = dict((owner.actor_id, rent) for owner, rent in world.land_rent_owners())
	return received.get(stratum.actor_id, 0.0) if received else None


def grievance_parts(stratum: Any, holders: List[Any], world: Any) -> Dict[str, float]:
	"""What the stratum earns by wages and by property, with its property income read from the land market's
	rent where land was let (else its share of the society's output)."""
	parts = income_parts(stratum, world)
	if PROPERTY in parts:
		rent = rent_of(stratum, holders, world)
		if rent is not None:
			parts[PROPERTY] = rent
	return parts
