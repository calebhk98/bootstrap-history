"""The actors module's rules: plain functions of their inputs."""
from typing import Any, Dict, Iterable, List, Optional, Tuple


def plain_number(value: float, digits: int = 0) -> str:
	"""A count, a number of people or of hours with thousands separators."""
	return format(value, ",.%df" % digits)


def founder_share_of_sellers(sellers: float, other_actors_concerns: float) -> float:
	"""The founder's share of the concerns selling into a category: every seller's concerns (`sellers`, the
	founder's included) less the other actors' (`other_actors_concerns`), over every seller's, held to 0..1."""
	return min(1.0, max(0.0, 1.0 - other_actors_concerns / sellers))


def nationwide_staff(home_staff: float, army_outside_pool: float) -> float:
	"""People of a trade that firms and governments hold nationwide: the slice they drew from the founder's reachable pool
	plus what the government's army holds beyond that slice (zero for any trade but the soldiers')."""
	return max(0.0, home_staff + army_outside_pool)


def conquest_contacts(places_by_country: Dict[Optional[str], List[Any]], previous: Optional[str], tile: str) -> List[str]:
	"""The places a conquest gives contact with: the tile and wherever the previous owner's actors are.
	`places_by_country` is {country: actor places}."""
	places = {str(tile)} | {str(place) for place in places_by_country.get(previous, ()) if place is not None}
	return sorted(places)


def migrants_arriving(pairs: Iterable[Tuple[str, str, float]], volume_per_person: float) -> Dict[str, Dict[str, float]]:
	"""{destination: {origin: contact volume}} from (origin, destination, people moved) pairs."""
	found: Dict[str, Dict[str, float]] = {}
	for origin, destination, moved in pairs:
		if moved > 0.0:
			by_origin = found.setdefault(destination, {})
			by_origin[origin] = by_origin.get(origin, 0.0) + moved * volume_per_person
	return found
