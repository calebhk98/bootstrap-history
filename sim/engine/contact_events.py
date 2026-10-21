"""Contact events the engine reports to the agents: a conquest or a migration raises the receivers' awareness of what
the people met know (`awareness.record_contact`). The rules for who receives and from which place are plain functions."""
from typing import Any, Dict, Iterable, List, Optional, Tuple

from sim.agents.api import CONQUEST_CONTACT_VOLUME, MIGRANT_CONTACT_VOLUME_PER_PERSON, awareness


def conquest_contacts(places_by_country: Dict[Optional[str], List[Any]], previous: Optional[str],
					  tile: str) -> List[str]:
	"""The places a conquest gives contact with: the tile and wherever the previous owner's actors are.
	`places_by_country` is {country: actor places}."""
	places = {str(tile)} | {str(place) for place in places_by_country.get(previous, ()) if place is not None}
	return sorted(places)


def after_conquest(sim: Any, conqueror: str, previous: Optional[str], tile: str) -> None:
	"""The winner's actors become aware of what the overrun country's people know."""
	registry = sim.actors
	places_by_country: Dict[Optional[str], List[Any]] = {}
	receivers = []
	for actor_id in sorted(registry.actors):
		actor = registry.actors[actor_id]
		country = registry.country_of(actor)
		places_by_country.setdefault(country, []).append(actor.location())
		if country == conqueror:
			receivers.append(actor)
	places = conquest_contacts(places_by_country, previous, tile)
	awareness.record_contacts(receivers, places, CONQUEST_CONTACT_VOLUME)


def migrants_arriving(pairs: Iterable[Tuple[str, str, float]]) -> Dict[str, Dict[str, float]]:
	"""{destination: {origin: contact volume}} from (origin, destination, people moved) pairs."""
	found: Dict[str, Dict[str, float]] = {}
	for origin, destination, moved in pairs:
		if moved > 0.0:
			by_origin = found.setdefault(destination, {})
			by_origin[origin] = by_origin.get(origin, 0.0) + moved * MIGRANT_CONTACT_VOLUME_PER_PERSON
	return found


def after_migration(sim: Any, pairs: Iterable[Tuple[str, str, float]]) -> None:
	"""Actors where migrants arrive become aware of what the people of the place the migrants left know."""
	arriving = migrants_arriving(pairs)
	if not arriving:
		return
	registry = sim.actors
	for actor_id in sorted(registry.actors):
		actor = registry.actors[actor_id]
		for origin, volume in sorted(arriving.get(actor.location(), {}).items()):
			awareness.record_contact(actor, origin, volume)
