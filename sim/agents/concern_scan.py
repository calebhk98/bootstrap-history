"""Whether the plants a business runs pay their way at today's prices (Complaints 528 and 510).

The scan reads a `Business`, the one object every owner's plants live in. The takings and costs of a plant are the
ones an entrant weighs (entry_round.NicheEntry): a lone operator's takings at full ramp, against the plant's upkeep,
its wage bill and what a firm carries (site rent and a manager's hours), times the plant's size.
"""
from typing import Any, Dict, Iterable, List, Optional, Tuple

from . import business_books, firm_entry
from .business import Business
from .business_plant import OPERATING


def plant_figures(business: Business, entry_key: str, registry: Any, world: Any, owner_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
	"""One plant's yearly figures at full ramp, as an entrant sees them, scaled to its size; None when the actor's country
	keeps no record of a cost."""
	tile = firm_entry.firm_tile(registry, None)
	size = business.size_of(entry_key)
	takings = world.entry_gross(entry_key, 0.0, 1.0) * size
	yearly = business_books.yearly_costs(world, entry_key)
	carried = firm_entry.carrying_cost(world, entry_key, tile=tile)
	if yearly is None or carried is None:   # the country keeps no record of a cost: the plant has no row
		return None
	upkeep, wages = yearly[0] * size, yearly[1] * size
	carried *= size
	costs = upkeep + wages + carried
	return {"node": entry_key, "owner": owner_id or business.owner_id, "size": size, "sells": bool(world.sells_on_book(entry_key)),
			"takings": takings, "upkeep": upkeep, "wages": wages, "carried": carried,
			"costs": costs, "margin": takings - costs, "pays": takings > costs}


def scan_business(business: Business, registry: Any, world: Any, owner_id: Optional[str] = None) -> List[Dict[str, Any]]:
	"""`plant_figures` of each plant the business is running, in entry order."""
	rows = (plant_figures(business, entry_key, registry, world, owner_id) for entry_key in sorted(business.entry_keys())
			if business.state_of(entry_key) == OPERATING)
	return [row for row in rows if row is not None]


def scan_businesses(businesses: Iterable[Tuple[str, Business]], registry: Any, world: Any) -> List[Dict[str, Any]]:
	"""The rows of several businesses given as (owner id, business), one business after another."""
	return [row for owner_id, business in businesses for row in scan_business(business, registry, world, owner_id)]


def summary(rows: List[Dict[str, Any]], biggest_losers: int = 10) -> Dict[str, Any]:
	"""{count, paying, selling (plants whose goods sell in the book), share (None for no plants), pay (the paying rows, best
	margin first), losers (the `biggest_losers` worst margins first)}."""
	paying = sorted((row for row in rows if row["pays"]), key=lambda row: (-row["margin"], row["node"]))
	losing = sorted((row for row in rows if not row["pays"]), key=lambda row: (row["margin"], row["node"]))
	return {"count": len(rows), "paying": len(paying), "selling": sum(1 for row in rows if row["sells"]),
			"share": len(paying) / len(rows) if rows else None, "pay": paying, "losers": losing[:biggest_losers]}
