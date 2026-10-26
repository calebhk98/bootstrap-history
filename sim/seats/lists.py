"""Which seats are still in the run, and the end rule for several seats.

A seat's run ends for that seat alone: its founder dies with no deputies to carry the work, is denounced, or
is brought down (the seat's `dead_reason`). The other seats keep playing. In an immortal-founder run no founder
dies, so the rule never fires. The run is over for the session when no seat is left playing, or every seat
still playing has reached its goal."""
from typing import Any, List, Mapping

MODULE_ID = "seats"


def goal_year_of(seat: Any) -> Any:
	"""The year the seat's formal goal was reached, or None."""
	return seat.modules[MODULE_ID].goal_year


def seat_ended(seat: Any) -> bool:
	"""Whether this seat's run has ended (its founder's death, a denunciation or a fall)."""
	return bool(seat.modules[MODULE_ID].dead_reason)


def seat_finished(seat: Any) -> bool:
	"""Whether this seat has nothing more to play: its run ended, or its goal was reached."""
	return seat_ended(seat) or goal_year_of(seat) is not None


def seats_playing(seats: Mapping[str, Any]) -> List[str]:
	"""Ids of the household seats whose run has not ended, in the fixed order they joined. A country seat is not
	among them: it has no household to run through the seat phases; its government acts with the actors' year."""
	return [seat_id for seat_id, seat in seats.items() if seat.holds_household and not seat_ended(seat)]


def seats_ended(seats: Mapping[str, Any]) -> List[str]:
	"""Ids of the seats whose run has ended, in joining order."""
	return [seat_id for seat_id, seat in seats.items() if seat_ended(seat)]


def run_is_over(seats: Mapping[str, Any]) -> bool:
	"""True when every household seat has ended or reached its goal (a country seat has neither); false with none."""
	households = [seat for seat in seats.values() if seat.holds_household]
	return bool(households) and all(seat_finished(seat) for seat in households)
