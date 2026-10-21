"""The state's collected share by tile, read from the world: its officials, their literacy, its people and the road.

Mixed into the home world and a country's view; each supplies `collection_people_by_tile` and `collection_modes`
(the people on each tile held, and the route modes its technologies open). The state's guards and inspectors reach a
tile by the same time rule (order.py).
"""
from typing import Any, Dict, Optional, Iterable

from sim.geography.api import reach

from . import budget, collection, order
from .revenue_labour import HOURS_PER_WORKING_DAY

ADMINISTRATION_LINE = "administration"
FAR_DAYS = 1.0e9


class CollectionView:
	"""What the officials of the state collect, tile by tile."""

	def collection_people_by_tile(self) -> Dict[str, float]:
		raise NotImplementedError

	def collection_modes(self) -> Iterable[str]:
		raise NotImplementedError

	def collection_world_map(self) -> Any:
		return None

	def staff_employed(self, line_name: str, trade: str, kept: float) -> float:
		"""Staff of a budget line on the payroll: those the line asks for, less the share it left unpaid."""
		record = self.government().record  # type: ignore[attr-defined]
		need = kept * self.pay_per_person_year(trade)  # type: ignore[attr-defined]
		return collection.officials_employed(kept, need, record.unfunded.get(line_name, 0.0))

	def officials_employed(self) -> float:
		"""Officials on the payroll: those the administration line asks for, less the share it left unpaid."""
		return self.staff_employed(ADMINISTRATION_LINE, "scribe", budget.officials_kept(self))

	def working_days_per_year(self) -> float:
		return order.working_days_of(self)

	def guards_employed(self) -> float:
		return self.staff_employed(order.GUARDS_LINE, order.GUARD_TRADE,
								   order.guards_kept(self.population_total(), self.working_days_per_year()))  # type: ignore[attr-defined]

	def inspectors_employed(self) -> float:
		return self.staff_employed(order.INSPECTORS_LINE, order.INSPECTOR_TRADE,
								   order.inspectors_kept(self.population_total(), self.working_days_per_year()))  # type: ignore[attr-defined]

	def foresters_employed(self) -> float:
		return self.staff_employed(order.FORESTERS_LINE, order.FORESTER_TRADE,
								   order.foresters_kept(self.population_total(), self.working_days_per_year()))  # type: ignore[attr-defined]

	def _collection_ground(self) -> Dict[str, Any]:
		"""The people on each tile and the days of road from the seat to it, kept for the year."""
		memo = self.__dict__.setdefault("_collection_memo", {})
		if "people" not in memo:
			people = self.collection_people_by_tile()
			seat = collection.seat_tile(people)
			modes = tuple(self.collection_modes())
			days: Dict[str, float] = {}
			if seat is not None:
				days = {seat: 0.0}
				if modes:
					days.update(reach([seat], modes, FAR_DAYS, world_map=self.collection_world_map()))
			memo["people"], memo["days"] = people, days
		return memo

	def collection_shares(self) -> Dict[str, float]:
		"""{tile: share of what is due there that the state collects} this year."""
		memo = self._collection_ground()
		if "shares" not in memo:
			memo["shares"] = collection.tile_shares(self.officials_employed(), self.working_days_per_year(),
													self.literacy("literacy_elite"), memo["people"], memo["days"])  # type: ignore[attr-defined]
		return memo["shares"]  # type: ignore[no-any-return]

	def collectible_share(self, tiles: Optional[Iterable[str]] = None) -> float:
		"""The share of what is due on `tiles` (all the state holds when none) that its officials collect."""
		shares = self.collection_shares()
		return collection.collectible_share(shares, self.__dict__["_collection_memo"]["people"], tiles)

	def order_share(self, tiles: Optional[Iterable[str]] = None) -> float:
		"""The share of the people on `tiles` (all the state holds when none) that its employed guards watch."""
		memo = self._collection_ground()
		if "order" not in memo:
			memo["order"] = collection.tile_shares(self.guards_employed(), self.working_days_per_year(), 0.0, memo["people"],
												   memo["days"], order.PATROL_DAYS_PER_PERSON)
		return collection.collectible_share(memo["order"], memo["people"], tiles)

	def inspection_share(self, tiles: Optional[Iterable[str]] = None) -> float:
		"""The share of the people on `tiles` (all the state holds when none) whose claims its employed inspectors check."""
		memo = self._collection_ground()
		if "inspection" not in memo:
			memo["inspection"] = collection.tile_shares(self.inspectors_employed(), self.working_days_per_year(), 0.0,
														memo["people"], memo["days"], order.INSPECTION_DAYS_PER_PERSON)
		return collection.collectible_share(memo["inspection"], memo["people"], tiles)

	def forest_share(self, tiles: Optional[Iterable[str]] = None) -> float:
		"""The share of the people on `tiles` (all the state holds when none) whose woodland tenure its employed foresters keep."""
		memo = self._collection_ground()
		if "forest" not in memo:
			memo["forest"] = collection.tile_shares(self.foresters_employed(), self.working_days_per_year(), 0.0, memo["people"],
													memo["days"], order.FORESTER_DAYS_PER_PERSON)
		return collection.collectible_share(memo["forest"], memo["people"], tiles)
