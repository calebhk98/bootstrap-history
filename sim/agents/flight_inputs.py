"""What the state's take looks like to a payer deciding whether to stay, tile by tile, and what leaving would cost him.

These read the state's present forms (levers included) and the officials' reach on each tile; the labour market's
migration rule (`sim/labour/market/migration.py`) turns them into flows. Any state, any tile.

    take_on_tile = sum over forms on income of rate * reach_on_tile            (at most all of it)
    share_taken_of_stayer = the liability rule's share at that take, registered payers and those who remain
"""
from typing import Any, Dict, Iterable, List, Mapping

from . import liability

INCOME_BASES = ("harvest", "stratum_income")   # forms whose take a worker's income bears as a share


def _covers(form: Mapping[str, Any], tile: str) -> bool:
	tiles, excepted = form.get("tiles"), form.get("except_tiles")
	return (tiles is None or tile in tiles) and tile not in (excepted or ())


def take_on_tile(forms: Iterable[Mapping[str, Any]], tile: str, reach: float) -> float:
	"""Share of income the state's forms on income would take on `tile` from payers its officials reach `reach` of."""
	rate = sum(float(form["rate"]) for form in forms if form["basis"] in INCOME_BASES and _covers(form, tile))
	return min(1.0, max(0.0, rate) * max(0.0, min(1.0, reach)))


def taxed_share_by_tile(forms: List[Mapping[str, Any]], reach_by_tile: Mapping[str, float], rule: str,
						registered_by_tile: Mapping[str, float], people_by_tile: Mapping[str, float]) -> Dict[str, float]:
	"""{tile: share of a stayer's income the state takes} for each tile the state holds people on, under its liability
	rule: those who left leave their assessment to the stayers where the rule is collective."""
	taken: Dict[str, float] = {}
	for tile in sorted(people_by_tile):
		own = take_on_tile(forms, tile, reach_by_tile.get(tile, 0.0))
		share = liability.stayers_share_taken(rule, own, registered_by_tile.get(tile, 0.0), people_by_tile[tile])
		if share is not None:
			taken[tile] = share
	return taken
