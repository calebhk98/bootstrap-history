"""Bonded people on the market (Complaints 644 and 648): where bondage is recognised, who is on offer, the purchase itself,
and the captives a campaign adds. A buyer is any ledger party (an employer's purse, or the economy's edge); the sale moves
people out of the bonded stratum, pays its owner the ask and pays the merchants who carried them the carriage. What an
owner asks and a buyer bids is worked out in the labour market (sim/labour/market/bonded_worth.py), not here."""
from typing import Any, Dict, List, Tuple

from sim.constants import declare

from . import ledger
from .strata_seed import has_bondage
from .stratum import stratum_id

CAPTIVE_SHARE_OF_DEFEATED_LOSSES = declare(
	"CAPTIVE_SHARE_OF_DEFEATED_LOSSES", 0.2, kind="engineering_estimate", unit="share of the people a beaten force loses",
	source="Wikipedia 'Battle of Cannae' (https://en.wikipedia.org/wiki/Battle_of_Cannae, opened 2026-11): Livy 48,200 Romans "
		"killed and 19,300 captured, 19,300 / 67,500 = 0.29; Polybius about 70,000 killed and 10,000 captured, "
		"10,000 / 80,000 = 0.125; Plutarch 50,000 killed and 4,000 + 10,000 captured, 14,000 / 64,000 = 0.22. Wikipedia 'Atuatuci' "
		"(https://en.wikipedia.org/wiki/Atuatuci): 4,000 killed and the surviving 53,000 sold, 0.93 of a besieged people.",
	confidence="C",
	why="Of the people a force loses in a defeat, this share is taken alive and, where the winner's society keeps bonded "
		"people, added to them. Field-battle accounts of one famous defeat give 0.125 to 0.29 (mean 0.21); a besieged people "
		"that cannot leave gives 0.93, so 0.2 is the field-battle ballpark. Counts are the ancient authors' own, from one "
		"battle; Scheidel 2005 (JRS 95) adds that women and children more often survived defeat than adult men.")

CAPTIVE_SHARE_OF_CONQUERED_PEOPLE = declare(
	"CAPTIVE_SHARE_OF_CONQUERED_PEOPLE", 0.02, kind="temporary_heuristic", unit="share of a taken tile's people",
	source="Sacked or besieged peoples carried off, from opened pages: Wikipedia 'Third Punic War' (50,000 survivors sold of a "
		"population estimated from 90,000 to 800,000, so 0.06 to 0.56); Wikipedia 'Atuatuci' (53,000 sold of a fortress holding "
		"at least 57,000, 0.93). A tile that surrendered under the custom of sparing those who yield before the ram touches the "
		"wall is not carried off in any case opened; no count of how many taken tiles were sacked was found.",
	confidence="D",
	why="When a tile is taken by force, this share of its people is carried off as bonded where the taker's society keeps "
		"bonded people. Where a place is sacked 0.06 to 0.93 of its people are sold (cases above); a tile taken by "
		"capitulation loses none. 0.02 is the average if about one taken tile in ten to fifteen is sacked, an "
		"assumption with no source, so the figure stays a labelled heuristic.",
	retire="648 captives by campaign record (Roman and other sources of prisoners taken per battle)")


def _recognises(registry: Any, country_key: str, profile: Any) -> bool:
	return has_bondage(profile) or bool(_bonded_strata(registry, country_key))


def bondage_tiles(registry: Any) -> Tuple[str, ...]:
	"""The home tiles of the countries that recognise bondage (their profile allows it, or they hold a bonded stratum), sorted."""
	tiles = set()
	for country_key, profile in registry.state.countries.items():
		if _recognises(registry, country_key, profile):
			tiles.update(profile.home_tiles)
	return tuple(sorted(tiles))


def _bonded_strata(registry: Any, country_key: str) -> List[Any]:
	return [actor for actor in registry.of_kind("stratum")
			if actor.is_bonded() and actor.record.members > 0.0 and actor.country_key() == country_key]


def bonded_for_sale(registry: Any) -> Dict[str, Dict[str, float]]:
	"""{tile: {trade: people}} the owners would sell at their price: every member of a bonded stratum (which names its
	trade), spread evenly over its country's home tiles. A country without home tiles offers none. How many are
	bought is the buyers' vacancies and the price, not a share set here."""
	offer: Dict[str, Dict[str, float]] = {}
	for country_key, profile in sorted(registry.state.countries.items()):
		if not profile.home_tiles:
			continue
		for actor in _bonded_strata(registry, country_key):
			trade = actor.record.plan.get("trade")
			if not trade:
				continue
			each = actor.record.members / len(profile.home_tiles)
			for tile in profile.home_tiles:
				by_trade = offer.setdefault(tile, {})
				by_trade[trade] = by_trade.get(trade, 0.0) + each
	return offer


def buy_bonded(registry: Any, buyer: Any, tile: str, trade: str, people: float, ask_per_person: float,
			   carriage_per_person: float = 0.0) -> float:
	"""The buyer takes up to `people` bonded of the trade from the strata of the country holding `tile`, paying each
	stratum's owner the ask for those taken and the country's merchants (the owner when it has none) the carriage.
	Returns the people bought."""
	if people <= 0.0 or ask_per_person < 0.0 or carriage_per_person < 0.0:
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
			cost_per_person = ask_per_person + carriage_per_person
			if cost_per_person > 0.0:   # the buyer takes no more people than it can pay for
				taken = min(taken, ledger.payable(buyer, taken * cost_per_person) / cost_per_person)
				if taken <= 0.0:
					continue
			owner = registry.actors.get(stratum_id(country_key, str(actor.record.plan.get("owner") or "")))
			if owner is None or owner is actor:
				continue
			carriers = registry.actors.get(stratum_id(country_key, "merchants")) or owner
			actor.record.members -= taken
			ledger.pay_up_to(buyer, owner, taken * ask_per_person, "purchase of bonded")
			if carriage_per_person > 0.0:
				ledger.pay_up_to(buyer, carriers, taken * carriage_per_person, "carriage of bonded")
			bought += taken
	return bought


def captives_from_losses(losses: float) -> float:
	"""People taken alive out of the `losses` a beaten force suffered."""
	return max(0.0, losses) * CAPTIVE_SHARE_OF_DEFEATED_LOSSES


def captives_from_conquest(people_of_tile: float) -> float:
	"""People carried off from a tile taken by force."""
	return max(0.0, people_of_tile) * CAPTIVE_SHARE_OF_CONQUERED_PEOPLE


def add_captives(registry: Any, country_key: str, people: float) -> float:
	"""`people` taken in war join the bonded stratum of the country that took them, where it has one; a society with no
	bonded stratum takes none into bondage. Returns the people added."""
	if people <= 0.0:
		return 0.0
	strata = [actor for actor in registry.of_kind("stratum") if actor.is_bonded() and actor.country_key() == country_key
			  and actor.record.exited_year is None]
	if not strata:
		return 0.0
	strata[0].record.members += people
	return people
