"""Which seats are still in the run, the end rule for several seats, and joining a seat.

A seat's run ends for that seat alone: its founder dies with no deputies to carry the work, is denounced, or
is brought down (`founder.dead_reason`). The other seats keep playing. In an immortal-founder run no founder
dies, so the rule never fires. The run is over for the session when no seat is left playing, or every seat
still playing has reached its goal."""
from typing import Iterable, List, Mapping

from .data import kit_capital
from .seat_country import partner_country_of_seat
from .seat_handover import SeatHandoverMixin
from .state_seat import COUNTRY_SEAT, SeatState, seat_from_template


def seat_ended(seat: SeatState) -> bool:
	"""Whether this seat's run has ended (its founder's death, a denunciation or a fall)."""
	return bool(seat.founder is not None and seat.founder.dead_reason)


def seat_finished(seat: SeatState) -> bool:
	"""Whether this seat has nothing more to play: its run ended, or its goal was reached."""
	return seat_ended(seat) or seat.seat_progress.goal_year is not None


def seats_playing(seats: Mapping[str, SeatState]) -> List[str]:
	"""Ids of the household seats whose run has not ended, in the fixed order they joined. A country seat is not
	among them: it has no household to run through the seat phases; its government acts with the actors' year."""
	return [seat_id for seat_id, seat in seats.items() if seat.holds_household and not seat_ended(seat)]


def run_is_over(seats: Mapping[str, SeatState]) -> bool:
	"""True when every household seat has ended or reached its goal (a country seat has neither); false with none."""
	households = [seat for seat in seats.values() if seat.holds_household]
	return bool(households) and all(seat_finished(seat) for seat in households)


class SeatRunMixin(SeatHandoverMixin):

	def playing_seats(self) -> List[str]:
		return seats_playing(self.state.seats)

	def ended_seats(self) -> List[str]:
		return [seat_id for seat_id, seat in self.state.seats.items() if seat_ended(seat)]

	def run_over(self) -> bool:
		return run_is_over(self.state.seats)

	def join_seat(self, seat_id: str, template: Mapping) -> SeatState:
		"""Add a player from data. `template` may carry `capital` (at this society's prices) or `kit`, `country`,
		`base_tile`, `starting_techs`, `scholars`, `artisans` and `goal`; nothing about the seat is named here."""
		missing = sorted(tech_id for tech_id in template.get("starting_techs") or () if tech_id not in self.nodes)
		if missing:
			raise ValueError("seat %r lists unknown starting technologies: %s" % (seat_id, ", ".join(missing)))
		if template.get("capital") is not None:
			capital = float(template["capital"]) * self.price_index
		elif template.get("kit"):
			capital = kit_capital(template["kit"], self.civ) * self.price_index
		else:
			capital = 0.0
		if template.get("kind") == COUNTRY_SEAT:
			country = template.get("country") or str(self.civ.get("id"))
			if country not in self.governed_countries():
				raise ValueError("seat %r: no government of %r to hold" % (seat_id, country))
			template = dict(template, country=None if country == self.civ.get("id") else country)
		seat = seat_from_template(template, capital, self._new_founder_years(), self._new_seat_policy())
		self.add_seat(seat_id, seat)
		with self.act_as(seat_id):
			self._wrap_seat_containers()
			if seat.kind == COUNTRY_SEAT:
				seat.holder = self.state_treasury().actor_id
		return seat

	def acting_country(self):
		"""The partner country the acting seat belongs to, or None for the game's own country: the markets,
		wages and prices the seat deals in are that country's own."""
		return partner_country_of_seat(self.state.seats, self.state.acting_seat, self.civ.get("id"))

	def governed_countries(self) -> List[str]:
		"""The countries that have a government a country seat can hold, the game's own first."""
		from .society_actors import seed_opening_cast
		seed_opening_cast(self)
		home = str(self.civ.get("id"))
		others = sorted(country for country in self.actors.state.countries if country != home)
		return [country for country in [home] + others if self.actors.government_of(country) is not None]

	def society_techs_now(self) -> set:
		"""The techniques the society holds now: what a seat joining today is granted."""
		return set(self._society_held_techs())

	def join_cast_seats(self) -> List[str]:
		"""Add the seats the civilisation's cast lists for the start of the game; returns their ids."""
		joined = []
		for template in (self.civ.get("cast") or {}).get("seats") or ():
			seat_id = template["id"]
			if seat_id not in self.state.seats:
				self.join_seat(seat_id, template)
				joined.append(seat_id)
		return joined

	def _new_founder_years(self) -> float:
		"""Years a new founder has left: effectively unlimited in an immortal run, else drawn like the first."""
		if self.cfg["immortal"]:
			return 1e9
		return max(self.FOUNDER_MIN_REMAINING_LIFE_YEARS,
		           self.rng.gauss(self.cfg["founder_life_mean"], self.cfg["founder_life_sd"]))

	def _new_seat_policy(self) -> dict:
		from .seat_defaults import default_policy
		return default_policy(self.manual)

	def each_playing_seat(self, seats: Iterable[str] = None):
		"""Yield each playing seat id with the seat acting for the body of the loop."""
		for seat_id in (self.playing_seats() if seats is None else list(seats)):
			with self.act_as(seat_id):
				yield seat_id
