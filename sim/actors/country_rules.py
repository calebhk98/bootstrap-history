"""What the cast answers about countries and their treasuries: plain functions of the registry or of written-out inputs."""
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from sim.agents.api import GOVERNMENT_PREFIX, CountryLiteracy, seed_strata
from sim.coin.api import visibility_factor
from sim.world import stock_dynamics


def is_country_with_state(owner: str, home_id: str, countries: Mapping[str, Any]) -> bool:
	"""Whether the owner is the home country or a country of the cast (a seat's colony or a bare owner has no soldiers to raise)."""
	return owner == home_id or owner in countries


def home_country_facts(home_country: str, countries: Mapping[str, Any]) -> Dict[str, Any]:
	"""{id: the home country's id, location: the tile at its centre, None when the cast has no such country}."""
	home = countries.get(home_country)
	return {"id": home_country, "location": None if home is None else home.location}


def organised_factions(groups: Sequence[Any], home_id: str, owner: str) -> List[Tuple[float, float]]:
	"""[(members, grievance)] of the organised interest groups whose country (the home country when unset) is the owner."""
	return [(group.record.members, group.record.grievance) for group in groups
	        if group.organised() and (group.record.country or home_id) == owner]


def treasury_account(holder: str, joined_seats: Sequence[str], government_id: Optional[str]) -> str:
	"""The account a holder's dues are paid into: a seat itself (paid as its party), else the holder country's government
	(`government_id`, or the id it would have when the cast holds none yet)."""
	if holder in joined_seats:
		return holder
	return government_id if government_id is not None else GOVERNMENT_PREFIX + str(holder)


def country_literacy(registry: Any, country: Optional[str]) -> CountryLiteracy:
	"""The reading shares of `country` (the home country when None), owned by the country's strata; the strata are founded
	first when the cast holds none."""
	if not registry.of_kind("stratum"):
		seed_strata(registry, None)
	home = registry.state.home_country
	country = country or home
	return CountryLiteracy(actor for actor in registry.of_kind("stratum") if (actor.record.country or home) == country)


def partner_catch_chance(registry: Any, world: Any, civilization_id: str, share_of_holding: float) -> float:
	"""Chance the partner's state finds out a taking of this share of what it holds: its reach (what its paid officials collect of
	what is due over its roads) against how visible the bite is."""
	reach = float(registry.world_for(registry.get(GOVERNMENT_PREFIX + civilization_id), world).state_reach())
	return stock_dynamics.catch_chance(reach, visibility_factor(share_of_holding))
