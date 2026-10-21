"""Whether each concern a society holds pays its way at today's prices (Complaint 528).

The takings and costs are the ones an entrant weighs (entry_round.NicheEntry): a lone operator's takings at full
ramp, against the concern's upkeep, its wage bill and what a firm carries (site rent and a manager's hours).
"""
from typing import Any, Dict, Iterable, List, Optional

from . import business_books, firm_entry


def concern_figures(registry: Any, world: Any, node_id: str) -> Optional[Dict[str, Any]]:
	"""One concern's yearly figures for a lone operator at full ramp, as an entrant sees them; None when the actor's country
	keeps no record of a cost."""
	tile = firm_entry.firm_tile(registry, None)
	takings = world.entry_gross(node_id, 0.0, 1.0)
	yearly = business_books.yearly_costs(world, node_id)
	carried = firm_entry.carrying_cost(world, node_id, tile=tile)
	if yearly is None or carried is None:   # the country keeps no record of a cost: the concern has no row
		return None
	upkeep, wages = yearly
	costs = upkeep + wages + carried
	return {"node": node_id, "takings": takings, "upkeep": upkeep, "wages": wages, "carried": carried,
			"costs": costs, "margin": takings - costs, "pays": takings > costs}


def scan(registry: Any, world: Any, node_ids: Iterable[str]) -> List[Dict[str, Any]]:
	"""`concern_figures` of each node that has them, in id order."""
	rows = (concern_figures(registry, world, node_id) for node_id in sorted(node_ids))
	return [row for row in rows if row is not None]


def summary(rows: List[Dict[str, Any]], biggest_losers: int = 10) -> Dict[str, Any]:
	"""{count, paying, share (None for no concerns), pay (the paying rows, best margin first), losers (the
	`biggest_losers` worst margins first)}."""
	paying = sorted((row for row in rows if row["pays"]), key=lambda row: (-row["margin"], row["node"]))
	losing = sorted((row for row in rows if not row["pays"]), key=lambda row: (row["margin"], row["node"]))
	return {"count": len(rows), "paying": len(paying), "share": len(paying) / len(rows) if rows else None,
			"pay": paying, "losers": losing[:biggest_losers]}
