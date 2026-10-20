"""`Business`: the plants an owner runs, the one record every owner's businesses are kept in.

A business belongs to an owner (a firm, a player, a state, ...) and holds its plants. The rules that act on it
(crew, books, closing) are in `business_crew.py`, `business_books.py` and `business_closing.py`; they are
functions of (business, owner, world), so the arithmetic is the same whoever the owner is. The registry hangs a
`watch` on a firm's or player's business so its indexes follow the plants it opens and closes.
"""
from collections.abc import MutableSet
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, Iterator, KeysView, List, Optional, Sequence

from . import business_review
from .business_views import Closures, StateKeys
from .business_plant import MOTHBALLED, OPERATING, Plant


@dataclass
class Business:
	business_id: str = ""
	owner_id: str = ""
	plants: List[Plant] = field(default_factory=list)

	def __post_init__(self) -> None:
		self._by_key: Dict[str, Plant] = {plant.entry_key: plant for plant in self.plants}
		# told after the set of plants changes (not saved; the registry sets it)
		self.watch: Optional[Callable[[], None]] = None
		self._views: Dict[str, Any] = {}

	@classmethod
	def running(cls, entry_keys: Iterable[str], opened_year: Optional[int] = None) -> "Business":
		"""A business already running a plant of each entry."""
		return cls(plants=[Plant(entry_key=key, opened_year=opened_year) for key in entry_keys])

	def _changed(self) -> None:
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

	# ---- reading ------------------------------------------------------------
	def entry_keys(self) -> KeysView:
		"""The entries it runs a plant of, in the order the plants were opened."""
		return self._by_key.keys()

	def plant_of(self, entry_key: str) -> Optional[Plant]:
		return self._by_key.get(entry_key)

	def sizes(self) -> Dict[str, float]:
		return {key: plant.size for key, plant in self._by_key.items()}

	def state_of(self, entry_key: str) -> Optional[str]:
		plant = self._by_key.get(entry_key)
		return None if plant is None else plant.state

	def opened_year_of(self, entry_key: str, default: int) -> int:
		plant = self._by_key.get(entry_key)
		return default if plant is None or plant.opened_year is None else plant.opened_year

	def size_of(self, entry_key: str) -> float:
		plant = self._by_key.get(entry_key)
		return 1.0 if plant is None else plant.size

	def crew_found_of(self, entry_key: str) -> float:
		plant = self._by_key.get(entry_key)
		return 1.0 if plant is None else plant.crew_found

	def margin_of(self, entry_key: str) -> Optional[float]:
		plant = self._by_key.get(entry_key)
		return None if plant is None else plant.margin

	# ---- changing -----------------------------------------------------------
	def open_plant(self, entry_key: str, year: Optional[int]) -> Plant:
		"""Begin running a plant of the entry from `year`; a plant already running is restarted from `year`,
		and a mothballed one is brought back with its size and age."""
		plant = self._by_key.get(entry_key)
		if plant is not None and plant.state == MOTHBALLED:
			self.restore(entry_key)
			return plant
		if plant is not None:
			plant.opened_year = year
			return plant
		plant = Plant(entry_key=entry_key, opened_year=year)
		self.plants.append(plant)
		self._by_key[entry_key] = plant
		self._changed()
		return plant

	def mothball(self, entry_key: str, year: Optional[int], reason: str) -> Plant:
		"""Switch the plant off, keeping its size and age; a plant that does not exist yet is made already switched off."""
		plant = self._by_key.get(entry_key)
		if plant is None:
			plant = Plant(entry_key=entry_key)
			self.plants.append(plant)
			self._by_key[entry_key] = plant
		plant.state, plant.since_year, plant.reason = MOTHBALLED, year, reason
		self._changed()
		return plant

	def restore(self, entry_key: str) -> Optional[Plant]:
		"""Switch a mothballed plant back on."""
		plant = self._by_key.get(entry_key)
		if plant is not None and plant.state != OPERATING:
			plant.state, plant.since_year, plant.reason = OPERATING, None, ""
			self._changed()
		return plant

	def forget_reason(self, entry_key: str, reason: Optional[str] = None) -> bool:
		"""Drop the record of why a plant is shut (only that reason's, when one is named)."""
		plant = self._by_key.get(entry_key)
		if plant is None or not plant.reason or (reason is not None and plant.reason != reason):
			return False
		plant.reason, plant.since_year = "", None
		return True

	def adopt(self, plant: Plant) -> None:
		"""Take over a plant, with its size and age, from another business."""
		known = self._by_key.get(plant.entry_key)
		if known is not None:
			self.plants[self.plants.index(known)] = plant
		else:
			self.plants.append(plant)
		self._by_key[plant.entry_key] = plant
		self._changed()

	def close_plant(self, entry_key: str) -> Optional[Plant]:
		"""Stop running the entry; the plant, with its size and staffing, is forgotten and handed back."""
		plant = self._by_key.pop(entry_key, None)
		if plant is not None:
			self.plants.remove(plant)
			self._changed()
		return plant

	def close_all(self) -> None:
		if self.plants:
			self.plants.clear()
			self._by_key.clear()
			self._changed()

	def set_size(self, entry_key: str, size: float) -> None:
		"""Resize a plant. The owner tells the registry, which totals sizes across owners."""
		self._by_key[entry_key].size = size

	def note_opened_year_if_unknown(self, entry_key: str, year: int) -> None:
		plant = self._by_key.get(entry_key)
		if plant is not None and plant.opened_year is None:
			plant.opened_year = year

	def set_opened_year(self, entry_key: str, year: Optional[int]) -> None:
		"""Date the plant's opening, running one if the entry has none."""
		plant = self._by_key.get(entry_key)
		if plant is None:
			plant = self.open_plant(entry_key, year)
		plant.opened_year = year

	def note_crew_found(self, entry_key: str, found: float) -> None:
		plant = self._by_key.get(entry_key)
		if plant is not None:
			plant.crew_found = found

	def note_takings(self, entry_key: str, takings: float) -> None:
		plant = self._by_key.get(entry_key)
		if plant is not None:
			plant.takings = takings

	def note_margin(self, entry_key: str, margin: float) -> None:
		plant = self._by_key.get(entry_key)
		if plant is not None:
			plant.margin = margin

	def note_year(self, entry_key: str, margin: float) -> None:
		"""Tally a plant's year: its margin, and how many years running it has lost money."""
		plant = self._by_key.get(entry_key)
		if plant is not None:
			plant.margin = margin
			plant.loss_years = plant.loss_years + 1 if margin < 0.0 else 0

	def longest_loss_run(self) -> int:
		"""The most consecutive loss years of any plant it runs."""
		return max((plant.loss_years for plant in self.plants if plant.state == OPERATING), default=0)

	def review(self, owner: Any, world: Any, rules: Sequence[str] = business_review.ALL_RULES) -> List[business_review.Closure]:
		"""Close the plants the rules shut for this owner (see `business_review`); what closed and why."""
		return business_review.review(self, owner, world, rules)

	def seize_all(self, owner: Any, world: Any) -> List[business_review.Closure]:
		"""The owner defaults and its creditors take every plant; what was taken."""
		return business_review.seize_all(self, owner, world)

	def review_reopening(self, owner: Any, world: Any) -> List[str]:
		"""Reopen the plants shut for want of staff that the owner can staff again; what reopened."""
		return business_review.reopen(self, owner, world)


class PlantKeys(MutableSet):
	"""An owner's `concerns`: the entries its business runs a plant of, as a set that opens and closes plants."""

	def __init__(self, business: Business) -> None:
		self._business = business

	@classmethod
	def _from_iterable(cls, iterable: Iterable[Any]) -> Any:
		return set(iterable)

	def __contains__(self, entry_key: object) -> bool:
		return entry_key in self._business.entry_keys()

	def __iter__(self) -> Iterator[str]:
		return iter(list(self._business.entry_keys()))

	def __len__(self) -> int:
		return len(self._business.entry_keys())

	def add(self, value: str) -> None:
		if value not in self._business.entry_keys():
			self._business.open_plant(value, None)

	def discard(self, value: str) -> None:
		self._business.close_plant(value)

	def clear(self) -> None:
		self._business.close_all()
