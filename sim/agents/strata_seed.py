"""Founding the strata of every country: from the profile's own list, else a default from what it states."""
from typing import Any, Dict, List

from .records import ActorRecord, CountryProfile
from .registry import register_spawner
from .stratum import stratum_id
from .stratum_year import settle_strata
from .tuning_strata import (DEFAULT_ARTISAN_SHARE_OF_URBAN, DEFAULT_BONDED_SHARE, DEFAULT_MERCHANT_SHARE_OF_URBAN,
							DEFAULT_POOR_SHARE, DEFAULT_POOR_WORK_SHARE, DEFAULT_RICH_PROPERTY_SHARE,
							DEFAULT_RICH_SHARE)

# the trades the default split's wage earners are paid as; a profile that declares its own strata
# names its own (labelled heuristic: a default until scenarios declare strata)
DEFAULT_TRADES = {"labourers": "labourer", "poor": "labourer", "artisans": "artisan", "merchants": "merchant"}


def has_bondage(profile: CountryProfile) -> bool:
	extra = profile.extra or {}
	return bool(extra.get("debt_bondage")) or float(extra.get("bondage_years") or 0.0) > 0.0


def strata_definitions(profile: CountryProfile) -> List[Dict[str, Any]]:
	"""The profile's strata as given, else a split derived from its population, urban share and literacy."""
	if profile.strata:
		return profile.strata
	urban = max(0.0, min(1.0, profile.urban_fraction))
	general, elite = profile.literacy_general, profile.literacy_elite
	bonded = DEFAULT_BONDED_SHARE if has_bondage(profile) else 0.0
	merchants = urban * DEFAULT_MERCHANT_SHARE_OF_URBAN
	artisans = urban * DEFAULT_ARTISAN_SHARE_OF_URBAN
	labourers = 1.0 - DEFAULT_RICH_SHARE - DEFAULT_POOR_SHARE - bonded - merchants - artisans
	definitions = [
		{"name": "rich", "share": DEFAULT_RICH_SHARE, "property_share": DEFAULT_RICH_PROPERTY_SHARE,
		 "literacy": elite, "falls_to": "merchants"},
		{"name": "merchants", "share": merchants, "trade": DEFAULT_TRADES["merchants"],
		 "literacy": 0.5 * (general + elite), "rises_to": "rich", "falls_to": "artisans"},
		{"name": "artisans", "share": artisans, "trade": DEFAULT_TRADES["artisans"], "literacy": general,
		 "rises_to": "merchants", "falls_to": "labourers"},
		{"name": "labourers", "share": labourers, "trade": DEFAULT_TRADES["labourers"], "literacy": general,
		 "own_plot": True, "rises_to": "artisans", "falls_to": "poor"},
		{"name": "poor", "share": DEFAULT_POOR_SHARE, "trade": DEFAULT_TRADES["poor"],
		 "work_share": DEFAULT_POOR_WORK_SHARE, "literacy": general, "rises_to": "labourers"},
	]
	if bonded > 0.0:
		definitions[-1]["falls_to"] = "bonded"
		definitions.append({"name": "bonded", "share": bonded, "bonded": True, "owner": "rich",
							"literacy": 0.0, "rises_to": "poor"})
	return [entry for entry in definitions if entry["share"] > 0.0]


def seed_strata(registry: Any, world: Any) -> List[str]:
	"""Found each country's missing strata; countries without a profile have nothing to derive them from."""
	home = registry.state.home_country
	founded = []
	for country in sorted(set(registry.state.countries) | ({home} if home else set())):
		profile = registry.state.countries.get(country)
		if profile is None:
			continue
		for entry in strata_definitions(profile):
			actor_id = stratum_id(country, entry["name"])
			if actor_id in registry.actors or entry.get("share", 0.0) <= 0.0:
				continue
			registry.add(actor_id, ActorRecord(
				kind="stratum", name="%s %s" % (profile.name or country, entry["name"]),
				country=None if country == home else country, stratum=entry["name"],
				members=float(entry["share"]) * profile.population,
				literacy=float(entry.get("literacy", profile.literacy_general)), plan=dict(entry)))
			founded.append(actor_id)
	return founded


def strata_spawner(registry: Any, world: Any) -> List[str]:
	"""The yearly step after every actor's turn: found missing strata, then settle moves and keep."""
	founded = seed_strata(registry, world)
	if registry.of_kind("stratum"):
		settle_strata(registry, world)
	return founded


register_spawner("strata", strata_spawner)
