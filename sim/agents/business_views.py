"""Views of a business's plants that read like the sets and mappings older code expects."""
from collections.abc import Mapping, MutableSet
from typing import Any, Dict, Iterator

from .business_plant import MOTHBALLED, OPERATING


class StateKeys(MutableSet):
	"""The entries whose plant is in one state, as a set that opens, mothballs and closes plants."""

	def __init__(self, business: Any, state: str) -> None:
		self._business = business
		self._state = state

	@classmethod
	def _from_iterable(cls, iterable: Any) -> Any:
		return set(iterable)

	def __contains__(self, entry_key: object) -> bool:
		plant = self._business.plant_of(entry_key)
		return plant is not None and plant.state == self._state

	def __iter__(self) -> Iterator[str]:
		return iter([plant.entry_key for plant in list(self._business.plants) if plant.state == self._state])

	def __len__(self) -> int:
		return sum(1 for plant in self._business.plants if plant.state == self._state)

	def add(self, value: str) -> None:
		if value in self:
			return
		if self._state == OPERATING:
			self._business.open_plant(value, None)
		else:
			self._business.mothball(value, None, "")

	def discard(self, value: str) -> None:
		if value in self:
			self._business.close_plant(value)

	def update(self, *others: Any) -> None:
		for other in others:
			for value in other:
				self.add(value)

	def intersection_update(self, *others: Any) -> None:
		for value in list(self):
			if not all(value in other for other in others):
				self.discard(value)

	def difference_update(self, *others: Any) -> None:
		for other in others:
			for value in list(other):
				self.discard(value)


class Closures(Mapping):
	"""Switched-off plants that record why, as {entry: {"reason", "year"}}; read only."""

	def __init__(self, business: Any) -> None:
		self._business = business

	def __getitem__(self, entry_key: str) -> Dict[str, object]:
		plant = self._business.plant_of(entry_key)
		if plant is None or plant.state != MOTHBALLED or not plant.reason:
			raise KeyError(entry_key)
		return {"reason": plant.reason, "year": plant.since_year}

	def __iter__(self) -> Iterator[str]:
		return iter([plant.entry_key for plant in list(self._business.plants)
		             if plant.state == MOTHBALLED and plant.reason])

	def __len__(self) -> int:
		return sum(1 for _ in self)
