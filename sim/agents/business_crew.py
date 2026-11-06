"""A business's crew: the places its plants need, posted to the labour market, and the people hired for them."""
from typing import Any

from .business import Business


def staff(business: Business, owner: Any, entry_key: str, world: Any, weight: float = 1.0) -> float:
	"""Post the places a plant needs (the labour core hires for them at the next clearing, paid there) and return the share
	of them the owner's people hired so far cover, which is the share of its output that gets made. `weight` is the share of
	the plant that runs the technique (its adoption share)."""
	size = business.reading.size_of(entry_key) * weight
	# a government holds its plants' inputs physically and finds them first; other owners buy theirs on the market
	input_found = owner.enterprises.input_share(entry_key, size, world) if owner.kind == "government" else 1.0
	found = input_found
	posted = owner.record.staff_wanted
	for trade, wanted in sorted(world.concerns.concern_staff(entry_key).items()):
		wanted *= size
		if wanted <= 0.0:
			continue
		before = posted.get(trade, 0.0)
		posted[trade] = before + wanted * input_found
		covered = max(0.0, owner.workforce.get(trade, 0.0) - before)
		found = min(found, covered / wanted)
	return found
