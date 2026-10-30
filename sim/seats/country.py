"""What country the acting seat plays for and what its state pays it: plain functions over the seats mapping."""
from typing import Any, Callable, List, Mapping, Optional, Tuple


def owner_of_seat(seats: Mapping[str, Any], seat_id: str, home_country: str) -> str:
	"""The country a seat raises armies and pays levies for: its own, else the game's."""
	return seats[seat_id].country or home_country


def partner_country_of_seat(seats: Mapping[str, Any], seat_id: str, home_country: str) -> Optional[str]:
	"""The partner country a seat belongs to, or None when it plays for the game's own country."""
	country = seats[seat_id].country
	return None if country in (None, home_country) else country


def patron_grant_share(grant_of: Callable[[str], Optional[float]], acting_country: Optional[str], acting_seat: str, home_country: str,
                       clients_of: Callable[[str], List[Tuple[str, float, float]]]) -> float:
	"""What the acting seat is paid by its country's state: the home state's whole grant, or a partner state's
	grant shared among the seats `clients_of(country)` lists; nothing when the acting seat is not among them or the
	state has no record (`grant_of` answers None). A seat with no country of its own is the home country's."""
	country = acting_country or home_country
	grant = grant_of(country)
	if grant is None:
		return 0.0
	if country == home_country:
		return grant
	clients = clients_of(country)
	return grant / len(clients) if any(seat_id == acting_seat for seat_id, _gov, _rep in clients) else 0.0
