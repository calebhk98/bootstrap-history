"""Bonded people on the market (Complaint 644): where bondage is recognised, how many a trade could buy, and
the purchase itself. A buyer is any ledger party (an employer's purse, or the economy's edge); the sale moves people
out of the bonded stratum and pays its owner.
"""
from typing import Any, Dict, List, Tuple

from sim.constants import declare

from . import ledger
from .strata_seed import has_bondage
from .stratum import stratum_id

BONDED_SALE_SHARE_PER_YEAR = declare(
	"BONDED_SALE_SHARE_PER_YEAR", 0.01, kind="temporary_heuristic", unit="share of a bonded stratum a year",
	source=None, confidence="D",
	why="No sale rule exists for the owners of the bonded: a fixed share of the bonded stratum is on offer "
		"each year, whatever its owners would gain or lose by selling.",
	retire="644 owners' sale rule")


def bondage_tiles(registry: Any) -> Tuple[str, ...]:
	"""The home tiles of the countries whose profile recognises bondage, sorted."""
	tiles = set()
	for profile in registry.state.countries.values():
		if has_bondage(profile):
			tiles.update(profile.home_tiles)
	return tuple(sorted(tiles))


def _bonded_strata(registry: Any, country_key: str) -> List[Any]:
	return [actor for actor in registry.of_kind("stratum")
			if actor.is_bonded() and actor.record.members > 0.0 and actor.country_key() == country_key]


def bonded_for_sale(registry: Any) -> Dict[str, Dict[str, float]]:
	"""{tile: {trade: people}} on offer: a share of each bonded stratum (which names its trade), spread evenly over
	its country's home tiles. A country without home tiles offers none."""
	offer: Dict[str, Dict[str, float]] = {}
	for country_key, profile in sorted(registry.state.countries.items()):
		if not profile.home_tiles:
			continue
		for actor in _bonded_strata(registry, country_key):
			trade = actor.record.plan.get("trade")
			if not trade:
				continue
			each = actor.record.members * BONDED_SALE_SHARE_PER_YEAR / len(profile.home_tiles)
			for tile in profile.home_tiles:
				by_trade = offer.setdefault(tile, {})
				by_trade[trade] = by_trade.get(trade, 0.0) + each
	return offer


def buy_bonded(registry: Any, buyer: Any, tile: str, trade: str, people: float, price_per_person: float) -> float:
	"""The buyer takes up to `people` bonded of the trade from the strata of the country holding `tile`, paying each
	stratum's owner the price for those taken. Returns the people bought."""
	if people <= 0.0 or price_per_person < 0.0:
		return 0.0
	bought = 0.0
	for country_key, profile in sorted(registry.state.countries.items()):
		if tile not in profile.home_tiles:
			continue
		for actor in _bonded_strata(registry, country_key):
			if actor.record.plan.get("trade") != trade:
				continue
			taken = min(people - bought, actor.record.members)
			if taken <= 0.0:
				continue
			owner = registry.actors.get(stratum_id(country_key, str(actor.record.plan.get("owner") or "")))
			if owner is None or owner is actor:
				continue
			actor.record.members -= taken
			ledger.transfer(buyer, owner, taken * price_per_person, "purchase of bonded")
			bought += taken
	return bought
