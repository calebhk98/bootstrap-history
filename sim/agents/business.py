"""`Business`: the plants an owner runs, the one record every owner's businesses are kept in.

A business belongs to an owner (a firm, a player, a state, ...) and holds its plants. The rules that act on it
(crew, books, closing) are in `business_crew.py`, `business_books.py` and `business_closing.py`; they are
functions of (business, owner, world), so the arithmetic is the same whoever the owner is. The registry hangs a
`watch` on a firm's or player's business so its indexes follow the plants it opens and closes.
"""
from collections.abc import MutableSet
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional

from .business_parts import PlantLifecycle, PlantReading, PlantReviews, PlantTally
from .business_views import Closures, StateKeys
from .business_plant import MOTHBALLED, OPERATING, Plant


@dataclass
class Business:
	business_id: str = ""
	owner_id: str = ""
	plants: List[Plant] = field(default_factory=list)

	def __post_init__(self) -> None:
		self.plant_by_entry: Dict[str, Plant] = {plant.entry_key: plant for plant in self.plants}
		# told after the set of plants changes (not saved; the registry sets it)
		self.watch: Optional[Callable[[], None]] = None
		self._views: Dict[str, Any] = {}
		self.reading = PlantReading(self)
		self.lifecycle = PlantLifecycle(self)
		self.tally = PlantTally(self)
		self.reviews = PlantReviews(self)

	@classmethod
	def running(cls, entry_keys: Iterable[str], opened_year: Optional[int] = None) -> "Business":
		"""A business already running a plant of each entry."""
		return cls(plants=[Plant(entry_key=key, opened_year=opened_year) for key in entry_keys])

	def note_plants_changed(self) -> None:
		if self.watch is not None:
			self.watch()

	def operating(self) -> Any:
		"""The entries with a plant running, as a set."""
		return self._view("operating", lambda: StateKeys(self, OPERATING))

	def mothballed(self) -> Any:
		"""The entries with a switched-off plant, as a set."""
		return self._view("mothballed", lambda: StateKeys(self, MOTHBALLED))

	def closures(self) -> Any:
		"""Switched-off plants that record why, as {entry: {"reason", "year"}}."""
		return self._view("closures", lambda: Closures(self))

	def _view(self, name: str, make: Callable[[], Any]) -> Any:
		if name not in self._views:
			self._views[name] = make()
		return self._views[name]


class PlantKeys(MutableSet):
	"""An owner's `concerns`: the entries its business runs a plant of, as a set that opens and closes plants."""

	def __init__(self, business: Business) -> None:
		self._business = business

	@classmethod
	def _from_iterable(cls, iterable: Iterable[Any]) -> Any:
		return set(iterable)

	def __contains__(self, entry_key: object) -> bool:
		return entry_key in self._business.reading.entry_keys()

	def __iter__(self) -> Iterator[str]:
		return iter(list(self._business.reading.entry_keys()))

	def __len__(self) -> int:
		return len(self._business.reading.entry_keys())

	def add(self, value: str) -> None:
		if value not in self._business.reading.entry_keys():
			self._business.lifecycle.open_plant(value, None)

	def discard(self, value: str) -> None:
		self._business.lifecycle.close_plant(value)

	def clear(self) -> None:
		self._business.lifecycle.close_all()
