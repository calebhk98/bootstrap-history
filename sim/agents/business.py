"""`Business`: the plants an owner runs, the one record every owner's businesses are kept in.

A business belongs to an owner (a firm, a player, a state, ...) and holds its plants. The rules that act on it
(crew, books, closing) are in `business_crew.py`, `business_books.py` and `business_closing.py`; they are
functions of (business, owner, world), so the arithmetic is the same whoever the owner is. The registry hangs a
`watch` on a firm's or player's business so its indexes follow the plants it opens and closes.
"""
from collections.abc import MutableSet
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, Iterator, KeysView, List, Optional

from .business_plant import Plant


@dataclass
class Business:
	business_id: str = ""
	owner_id: str = ""
	plants: List[Plant] = field(default_factory=list)

	def __post_init__(self) -> None:
		self._by_key: Dict[str, Plant] = {plant.entry_key: plant for plant in self.plants}
		# told after the set of plants changes (not saved; the registry sets it)
		self.watch: Optional[Callable[[], None]] = None

	@classmethod
	def running(cls, entry_keys: Iterable[str], opened_year: Optional[int] = None) -> "Business":
		"""A business already running a plant of each entry."""
		return cls(plants=[Plant(entry_key=key, opened_year=opened_year) for key in entry_keys])

	def _changed(self) -> None:
		if self.watch is not None:
			self.watch()

	# ---- reading ------------------------------------------------------------
	def entry_keys(self) -> KeysView:
		"""The entries it runs a plant of, in the order the plants were opened."""
		return self._by_key.keys()

	def plant_of(self, entry_key: str) -> Optional[Plant]:
		return self._by_key.get(entry_key)

	def sizes(self) -> Dict[str, float]:
		return {key: plant.size for key, plant in self._by_key.items()}

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
		"""Begin running a plant of the entry from `year`; a plant already running is restarted from `year`."""
		plant = self._by_key.get(entry_key)
		if plant is not None:
			plant.opened_year = year
			return plant
		plant = Plant(entry_key=entry_key, opened_year=year)
		self.plants.append(plant)
		self._by_key[entry_key] = plant
		self._changed()
		return plant

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

	def note_crew_found(self, entry_key: str, found: float) -> None:
		plant = self._by_key.get(entry_key)
		if plant is not None:
			plant.crew_found = found

	def note_margin(self, entry_key: str, margin: float) -> None:
		plant = self._by_key.get(entry_key)
		if plant is not None:
			plant.margin = margin


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
