"""A business's crew: the people its plants need, taken from the shared labour pool."""
from typing import Any

from .business import Business


def staff(business: Business, owner: Any, entry_key: str, world: Any, weight: float = 1.0) -> float:
	"""Take on the people a plant needs from the shared pool; the share of them found, which is the share
	of its output that gets made. `weight` is the share of the plant that runs the technique (its adoption share)."""
	size = business.size_of(entry_key) * weight
	inputs = getattr(owner, "input_share", None)   # an owner that holds its plants' inputs physically finds them first
	found = 1.0 if inputs is None else inputs(entry_key, size, world)
	for trade, wanted in sorted(world.concern_staff(entry_key).items()):
		wanted *= size
		free = world.free_fte(trade, owner.actor_id)
		if free is None or wanted <= 0.0:
			continue
		free -= owner.workforce.get(trade, 0.0)
		taken = min(wanted * found, max(0.0, free))
		owner.workforce[trade] = owner.workforce.get(trade, 0.0) + taken
		found = min(found, taken / wanted)
	return found
