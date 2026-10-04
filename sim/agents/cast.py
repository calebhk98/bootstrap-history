"""The game's roster as data: countries and the actors they start with, built from civilisation dicts.

Pure functions. A civilisation file may carry an optional "cast" key: {"strata": [...], "treasury": money,
"location": place, "countries": [civilisation-like dicts for countries with no file of their own],
"actors": [CastEntry-like dicts, for example a second player]}. Nothing here names a civilisation.
"""
import copy
import dataclasses
from typing import Any, Dict, List, Mapping, Optional, Tuple

from .records import ActorRecord, CastEntry, CountryProfile

# keys under "cast" this module reads itself; any others end up in the profile's `extra`
CONSUMED_CAST_KEYS = ("strata", "countries", "actors", "treasury", "location")
# civilisation keys kept in a profile's `extra` for the mechanisms that read them
CARRIED_CIVILISATION_KEYS = ("standing_army", "values", "debt_bondage", "bondage_years")
GOVERNMENT_PREFIX = "government:"
HOME_GOVERNMENT_KIND = "government"
FOREIGN_GOVERNMENT_KIND = "foreign_government"


def _number(value: Any, default: float) -> float:
	try:
		return float(value)
	except (TypeError, ValueError):
		return default


def profile_from_civilisation(civ: Mapping[str, Any]) -> CountryProfile:
	"""What a country starts with, read from its civilisation dict; missing keys take neutral values."""
	cast = civ.get("cast") or {}
	country = str(civ.get("id") or "")
	regions = [str(region) for region in civ.get("home_regions") or ()]
	extra: Dict[str, Any] = {key: copy.deepcopy(civ[key]) for key in CARRIED_CIVILISATION_KEYS if key in civ}
	extra.update({key: copy.deepcopy(value) for key, value in cast.items() if key not in CONSUMED_CAST_KEYS})
	return CountryProfile(
		country=country, name=str(civ.get("name") or country),
		population=_number(civ.get("population"), 0.0), urban_fraction=_number(civ.get("urban_fraction"), 0.0),
		state_capacity=_number(civ.get("state_capacity"), 0.0), tax_share=_number(civ.get("starting_tax_share"), 0.0),
		wage_index=_number(civ.get("wage_index"), 1.0), price_index=_number(civ.get("price_index"), 1.0),
		literacy_general=_number(civ.get("literacy_general"), 0.0), literacy_elite=_number(civ.get("literacy_elite"), 0.0),
		home_regions=regions, location=cast.get("location") or (regions[0] if regions else None),
		starting_techs={str(node_id) for node_id in civ.get("starting_techs") or ()},
		strata=[dict(stratum) for stratum in cast.get("strata") or ()], extra=extra)


def _entry_from_declaration(declared: Mapping[str, Any], default_country: Optional[str]) -> Optional[CastEntry]:
	"""A CastEntry from a declared dict; fields it does not know go to `params`. None if it names no actor."""
	if not declared.get("actor_id"):
		return None
	field_names = {field.name for field in dataclasses.fields(CastEntry)}
	known = {key: copy.deepcopy(value) for key, value in declared.items() if key in field_names and key != "params"}
	params = copy.deepcopy(dict(declared.get("params") or {}))
	params.update({key: copy.deepcopy(value) for key, value in declared.items() if key not in field_names})
	known.setdefault("country", default_country)
	return CastEntry(params=params, **known)


def cast_from_civilisations(home_civ: Mapping[str, Any], foreign_civs: List[Mapping[str, Any]]
							) -> Tuple[str, List[CastEntry], Dict[str, CountryProfile]]:
	"""(home country id, entries, profiles) for a game: a government per country, then whatever the
	civilisations declare under their "cast" keys. The home country's entries carry country None."""
	home_country = str(home_civ.get("id") or "")
	entries: List[CastEntry] = []
	profiles: Dict[str, CountryProfile] = {}
	pending = [home_civ] + list(foreign_civs)
	declared_actors: List[CastEntry] = []
	index = 0
	while index < len(pending):
		civ = pending[index]
		index += 1
		profile = profile_from_civilisation(civ)
		if not profile.country or profile.country in profiles:
			continue
		profiles[profile.country] = profile
		at_home = profile.country == home_country
		cast = civ.get("cast") or {}
		entries.append(CastEntry(
			actor_id=GOVERNMENT_PREFIX + profile.country, country=None if at_home else profile.country,
			kind=HOME_GOVERNMENT_KIND if at_home else FOREIGN_GOVERNMENT_KIND, name=profile.name,
			money=_number(cast.get("treasury"), 0.0), location=profile.location))
		pending.extend(cast.get("countries") or ())
		for declared in cast.get("actors") or ():
			entry = _entry_from_declaration(declared, None if at_home else profile.country)
			if entry is not None:
				declared_actors.append(entry)
	seen = {entry.actor_id for entry in entries}
	for entry in declared_actors:
		if entry.actor_id not in seen:
			seen.add(entry.actor_id)
			entries.append(entry)
	return home_country, entries, profiles


def _record_for(entry: CastEntry) -> ActorRecord:
	"""A fresh record for an entry; `params` fill the record fields they are named after."""
	record = ActorRecord(kind=entry.kind, name=entry.name or entry.actor_id, country=entry.country,
						 controller=entry.controller, policy_kind=entry.policy_kind, location=entry.location)
	field_names = {field.name for field in dataclasses.fields(ActorRecord)}
	for key, value in entry.params.items():
		if key in field_names and key != "money":
			value = copy.deepcopy(value)
			setattr(record, key, set(value) if isinstance(getattr(record, key), set) else value)
	return record


def seed_cast(registry: Any, home_country: str, entries: List[CastEntry],
			  profiles: Mapping[str, CountryProfile]) -> List[str]:
	"""Store the roster in the registry's state and create the actors it names; the ids created.

	Safe to repeat: an actor that exists is left alone, and a second call creates nothing. Opening money
	comes from outside the modelled actors, so it is booked as the edge "edge:opening". An entry whose kind
	is not registered yet stays in the roster and is created by a later call once the kind exists.
	"""
	from .registry import ACTOR_CLASSES
	state = registry.state
	state.home_country = home_country
	for country, profile in profiles.items():
		state.countries.setdefault(country, copy.deepcopy(profile))
	created: List[str] = []
	for entry in entries:
		state.cast.setdefault(entry.actor_id, copy.deepcopy(entry))
		if entry.actor_id in registry.actors or entry.actor_id in state.records or entry.kind not in ACTOR_CLASSES:
			continue
		actor = registry.add(entry.actor_id, _record_for(entry))
		if entry.money:
			actor.credit(_number(entry.money, 0.0), "edge:opening")
		created.append(entry.actor_id)
	return created
