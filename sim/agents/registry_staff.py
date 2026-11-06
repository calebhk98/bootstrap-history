"""`RegistryStaff`: the tally of every actor's staff by trade, kept current as single actors' staff change.

Reached as `registry.staff`. Per trade it keeps every actor's staff in id order and the running left-to-right sum of it, and
re-sums from the one actor whose staff changed, so the total is the same float a full count in id order gives.
"""
from bisect import bisect_left
from itertools import accumulate
from typing import Any, Dict, List, Optional, Set


class RegistryStaff:

	def __init__(self, registry: Any) -> None:
		self.registry = registry
		self._staff: Optional[Dict[str, float]] = None
		self._columns: Dict[str, Any] = {}
		self._column_position: Dict[str, int] = {}
		self._changed_actors: Set[str] = set()
		self._columns_synced = False
		self._acting: Optional[Any] = None
		self._staff_basis: Dict[str, float] = {}

	def refresh_staff(self) -> None:
		"""Forget the staffing and demand tallies so the next read counts every actor again."""
		self._staff = None
		self._columns = {}
		self._changed_actors = set()
		self._columns_synced = False

	def workforces(self) -> Dict[str, Dict[str, float]]:
		"""Each actor's staff by trade, copied."""
		return {actor_id: dict(actor.workforce) for actor_id, actor in self.registry.actors.items()}

	def begin_turn(self, actor: Any) -> None:
		"""The tally counts everyone's staff as of this acting actor's staff now."""
		self._acting, self._staff_basis = actor, dict(actor.workforce)

	def end_turn(self, actor: Any, first: bool) -> None:
		"""The tally stays when the acting actor's staff is what the count saw; the first actor of a year always recounts,
		since anything between years is unseen."""
		if first:
			self.refresh_staff()
		elif actor.workforce != self._staff_basis:
			self._staff = None
			self._changed_actors.add(actor.actor_id)
			self._columns_synced = False

	def end_year(self, before: Dict[str, Dict[str, float]]) -> None:
		"""Entry and group formation change staff after the last count; whatever reads before the next year's first actor
		sees what is there, as a reloaded game does. A year in which no actor's staff differs from the year's start leaves
		the tally standing."""
		if self.workforces() != before:
			self.refresh_staff()

	def stop_turns(self) -> None:
		"""No actor is acting."""
		self._acting = None

	def actor_added(self, actor_id: str, prior_order: Optional[List[str]], new: bool) -> None:
		"""A wrapped actor joined or was replaced: add a new one to the columns, else count again."""
		registry = self.registry
		if new and self._columns and prior_order is not None and len(prior_order) == len(registry.actors) - 1:
			self._insert_into_columns(actor_id, prior_order)
		else:
			self.refresh_staff()

	def _staff_total(self, trade: str) -> float:
		"""People of one trade across every actor, summed left to right in actor-id order, as
		`staff_by_trade` sums them, but as of the same moments: the actors' staff as read at the
		first count after a change, the acting actor's as it stood then."""
		acting = self._acting
		actors = self.registry.actors
		if not self._columns_synced:
			if acting is not None:
				self._staff_basis = dict(acting.workforce)
			changed = self._changed_actors
			if acting is not None:
				changed = changed | {acting.actor_id}
			for actor_id in changed:
				self._resum_actor(actor_id)
			self._changed_actors = set()
			self._columns_synced = True
		column = self._columns.get(trade)
		if column is None:
			ordered_ids = self.registry.sorted_ids()
			self._current_positions()
			values = [actors[actor_id].record.workforce.get(trade, 0.0) for actor_id in ordered_ids]
			if acting is not None:
				values[self._column_position[acting.actor_id]] = self._staff_basis.get(trade, 0.0)
			column = self._columns[trade] = (values, list(accumulate(values, initial=0.0)))
		return column[1][-1]

	def _current_positions(self) -> None:
		"""Make `_column_position` match the actor-id order."""
		ordered_ids = self.registry.sorted_ids()
		if len(self._column_position) != len(ordered_ids):
			self._column_position = {actor_id: place for place, actor_id in enumerate(ordered_ids)}

	def _insert_into_columns(self, actor_id: str, order: List[str]) -> None:
		"""Add one new actor to the id order and to every counted trade's column, re-summing
		from its place; the next count then re-reads the acting actor's staff."""
		place = bisect_left(order, actor_id)
		order.insert(place, actor_id)
		self.registry.ordered_ids = order
		self._column_position = {}
		staff = self.registry.actors[actor_id].record.workforce
		for trade, (values, running) in self._columns.items():
			values.insert(place, staff.get(trade, 0.0))
			running[place + 1:] = list(accumulate(values[place:], initial=running[place]))[1:]
		self._staff = None
		self._columns_synced = False

	def _resum_actor(self, actor_id: str) -> None:
		"""Bring every counted trade's column up to the actor's present staff."""
		actor = self.registry.actors.get(actor_id)
		self._current_positions()
		place = self._column_position.get(actor_id)
		if actor is None or place is None:
			self._columns = {}
			return
		staff = actor.record.workforce
		for trade, (values, running) in self._columns.items():
			people = staff.get(trade, 0.0)
			if people != values[place]:
				values[place] = people
				running[place + 1:] = list(accumulate(values[place:], initial=running[place]))[1:]

	def staff_by_trade(self) -> Dict[str, float]:
		"""People of each trade every recorded actor employs, in full-time equivalents."""
		if self._staff is None:
			totals: Dict[str, float] = {}
			actors = self.registry.actors
			for actor_id in self.registry.sorted_ids():
				for trade, people in actors[actor_id].record.workforce.items():
					totals[trade] = totals.get(trade, 0.0) + people
			self._staff = totals
			if self._acting is not None:
				self._staff_basis = dict(self._acting.workforce)
		return self._staff

	def staff_fte(self, trade: str, excluding: Optional[str] = None) -> float:
		"""People of one trade the actors employ, leaving out one actor's own staff."""
		total = self._staff_total(trade)
		actors = self.registry.actors
		if excluding is not None and excluding in actors:
			total -= actors[excluding].workforce.get(trade, 0.0)
		return max(0.0, total)

	def staff_fte_in_country(self, trade: str, country: str, excluding: Optional[str] = None) -> float:
		"""People of one trade the actors of one country employ, leaving out one actor's own staff."""
		countries = self.registry.countries
		total = sum(actor.workforce.get(trade, 0.0) for actor_id, actor in sorted(self.registry.actors.items())
					if actor_id != excluding and countries.country_of(actor) == country)
		return max(0.0, total)

	def home_staff_fte(self, trade: str, excluding: Optional[str] = None) -> float:
		"""People of one trade the home country's actors employ (an actor with no country is home)."""
		return self.staff_fte_in_country(trade, self.registry.state.home_country, excluding)
