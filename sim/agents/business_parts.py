"""The parts of a `Business`, each addressed as `business.<part>.<method>`:

    reading    what plants it runs and their sizes, ages, crews and margins
    lifecycle  opening, switching off, handing over and closing plants
    tally      the figures its owner keeps on a plant
    reviews    the reviews that shut or reopen plants (`business_review.py`)
"""
from typing import Any, Dict, KeysView, List, Optional, Sequence

from . import business_review
from .business_plant import MOTHBALLED, OPERATING, Plant


class PlantReading:
	"""Reads of the plants a business runs."""

	def __init__(self, business: Any) -> None:
		self.business = business

	def entry_keys(self) -> KeysView:
		"""The entries it runs a plant of, in the order the plants were opened."""
		return self.business.plant_by_entry.keys()

	def plant_of(self, entry_key: str) -> Optional[Plant]:
		return self.business.plant_by_entry.get(entry_key)

	def sizes(self) -> Dict[str, float]:
		return {key: plant.size for key, plant in self.business.plant_by_entry.items()}

	def state_of(self, entry_key: str) -> Optional[str]:
		plant = self.business.plant_by_entry.get(entry_key)
		return None if plant is None else plant.state

	def opened_year_of(self, entry_key: str, default: int) -> int:
		plant = self.business.plant_by_entry.get(entry_key)
		return default if plant is None or plant.opened_year is None else plant.opened_year

	def size_of(self, entry_key: str) -> float:
		plant = self.business.plant_by_entry.get(entry_key)
		return 1.0 if plant is None else plant.size

	def crew_found_of(self, entry_key: str) -> float:
		plant = self.business.plant_by_entry.get(entry_key)
		return 1.0 if plant is None else plant.crew_found

	def margin_of(self, entry_key: str) -> Optional[float]:
		plant = self.business.plant_by_entry.get(entry_key)
		return None if plant is None else plant.margin

	def longest_loss_run(self) -> int:
		"""The most consecutive loss years of any plant it runs."""
		return max((plant.loss_years for plant in self.business.plants if plant.state == OPERATING), default=0)


class PlantLifecycle:
	"""Opening, switching off, handing over and closing plants."""

	def __init__(self, business: Any) -> None:
		self.business = business

	def open_plant(self, entry_key: str, year: Optional[int], tile: Optional[str] = None) -> Plant:
		"""Begin running a plant of the entry from `year` on `tile` (where its owner is when none is given); a plant
		already running is restarted from `year`, and a mothballed one is brought back with its size and age."""
		plant = self.business.plant_by_entry.get(entry_key)
		if plant is not None and plant.state == MOTHBALLED:
			self.business.lifecycle.restore(entry_key)
			return plant
		if plant is not None:
			plant.opened_year = year
			return plant
		plant = Plant(entry_key=entry_key, opened_year=year, tile=tile)
		self.business.plants.append(plant)
		self.business.plant_by_entry[entry_key] = plant
		self.business.note_plants_changed()
		return plant

	def mothball(self, entry_key: str, year: Optional[int], reason: str) -> Plant:
		"""Switch the plant off, keeping its size and age; a plant that does not exist yet is made already switched off."""
		plant = self.business.plant_by_entry.get(entry_key)
		if plant is None:
			plant = Plant(entry_key=entry_key)
			self.business.plants.append(plant)
			self.business.plant_by_entry[entry_key] = plant
		plant.state, plant.since_year, plant.reason = MOTHBALLED, year, reason
		self.business.note_plants_changed()
		return plant

	def restore(self, entry_key: str) -> Optional[Plant]:
		"""Switch a mothballed plant back on."""
		plant = self.business.plant_by_entry.get(entry_key)
		if plant is not None and plant.state != OPERATING:
			plant.state, plant.since_year, plant.reason = OPERATING, None, ""
			self.business.note_plants_changed()
		return plant

	def forget_reason(self, entry_key: str, reason: Optional[str] = None) -> bool:
		"""Drop the record of why a plant is shut (only that reason's, when one is named)."""
		plant = self.business.plant_by_entry.get(entry_key)
		if plant is None or not plant.reason or (reason is not None and plant.reason != reason):
			return False
		plant.reason, plant.since_year = "", None
		return True

	def adopt(self, plant: Plant) -> None:
		"""Take over a plant, with its size and age, from another business."""
		known = self.business.plant_by_entry.get(plant.entry_key)
		if known is not None:
			self.business.plants[self.business.plants.index(known)] = plant
		else:
			self.business.plants.append(plant)
		self.business.plant_by_entry[plant.entry_key] = plant
		self.business.note_plants_changed()

	def close_plant(self, entry_key: str) -> Optional[Plant]:
		"""Stop running the entry; the plant, with its size and staffing, is forgotten and handed back."""
		plant = self.business.plant_by_entry.pop(entry_key, None)
		if plant is not None:
			self.business.plants.remove(plant)
			self.business.note_plants_changed()
		return plant

	def close_all(self) -> None:
		if self.business.plants:
			self.business.plants.clear()
			self.business.plant_by_entry.clear()
			self.business.note_plants_changed()


class PlantTally:
	"""Figures the owner keeps on its plants: size, dates, crew found, takings, margin."""

	def __init__(self, business: Any) -> None:
		self.business = business

	def set_size(self, entry_key: str, size: float) -> None:
		"""Resize a plant. The owner tells the registry, which totals sizes across owners."""
		self.business.plant_by_entry[entry_key].size = size

	def note_opened_year_if_unknown(self, entry_key: str, year: int) -> None:
		plant = self.business.plant_by_entry.get(entry_key)
		if plant is not None and plant.opened_year is None:
			plant.opened_year = year

	def set_opened_year(self, entry_key: str, year: Optional[int]) -> None:
		"""Date the plant's opening, running one if the entry has none."""
		plant = self.business.plant_by_entry.get(entry_key)
		if plant is None:
			plant = self.business.lifecycle.open_plant(entry_key, year)
		plant.opened_year = year

	def note_crew_found(self, entry_key: str, found: float) -> None:
		plant = self.business.plant_by_entry.get(entry_key)
		if plant is not None:
			plant.crew_found = found

	def note_takings(self, entry_key: str, takings: float) -> None:
		plant = self.business.plant_by_entry.get(entry_key)
		if plant is not None:
			plant.takings = takings

	def note_margin(self, entry_key: str, margin: float) -> None:
		plant = self.business.plant_by_entry.get(entry_key)
		if plant is not None:
			plant.margin = margin

	def note_year(self, entry_key: str, margin: float) -> None:
		"""Tally a plant's year: its margin, and how many years running it has lost money."""
		plant = self.business.plant_by_entry.get(entry_key)
		if plant is not None:
			plant.margin = margin
			plant.loss_years = plant.loss_years + 1 if margin < 0.0 else 0


class PlantReviews:
	"""The reviews that shut or reopen an owner's plants (`business_review.py`)."""

	def __init__(self, business: Any) -> None:
		self.business = business

	def review(self, owner: Any, rules: Sequence[str] = business_review.ALL_RULES) -> List[business_review.Closure]:
		"""Close the plants the rules shut for this owner (see `business_review`); what closed and why."""
		return business_review.review(self.business, owner, rules)

	def seize_all(self, owner: Any) -> List[business_review.Closure]:
		"""The owner defaults and its creditors take every plant; what was taken."""
		return business_review.seize_all(self.business, owner)

	def review_reopening(self, owner: Any) -> List[str]:
		"""Reopen the plants shut for want of staff that the owner can staff again; what reopened."""
		return business_review.reopen(self.business, owner)
