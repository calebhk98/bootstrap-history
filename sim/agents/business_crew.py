"""A business's crew: the people its plants need, taken from the shared labour pool."""
from typing import Any

from .business import Business


def staff(business: Business, owner: Any, entry_key: str, world: Any) -> float:
	"""Take on the people a plant needs from the shared pool; the share of them found, which is the share
	of its output that gets made."""
	found = 1.0
	size = business.size_of(entry_key)
	for trade, wanted in sorted(world.concern_staff(entry_key).items()):
		wanted *= size
		free = world.free_fte(trade, owner.actor_id)
		if free is None:
			continue
		free -= owner.workforce.get(trade, 0.0)
		taken = min(wanted, max(0.0, free))
		owner.workforce[trade] = owner.workforce.get(trade, 0.0) + taken
		found = min(found, taken / wanted)
	return found
