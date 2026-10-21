"""The state's collected share by tile, read from the world: its officials, their literacy, its people and the road.

Mixed into the home world and a country's view; each supplies `collection_people_by_tile` and `collection_modes`
(the people on each tile held, and the route modes its technologies open).
"""
from typing import Any, Dict, Optional, Iterable

from sim.geography.api import reach

from . import budget, collection
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

	def officials_employed(self) -> float:
		"""Officials on the payroll: those the administration line asks for, less the share it left unpaid."""
		record = self.government().record  # type: ignore[attr-defined]
		kept = budget.officials_kept(self)
		pay = self.pay_per_person_year("scribe")  # type: ignore[attr-defined]
		need = kept * pay
		return collection.officials_employed(kept, need, record.unfunded.get(ADMINISTRATION_LINE, 0.0))

	def collection_shares(self) -> Dict[str, float]:
		"""{tile: share of what is due there that the state collects} this year."""
		memo = self.__dict__.setdefault("_collection_memo", {})
		if "shares" not in memo:
			people = self.collection_people_by_tile()
			seat = collection.seat_tile(people)
			modes = tuple(self.collection_modes())
			days: Dict[str, float] = {}
			if seat is not None:
				days = {seat: 0.0}
				if modes:
					days.update(reach([seat], modes, FAR_DAYS, world_map=self.collection_world_map()))
			working_days = self.hours_per_person_year / HOURS_PER_WORKING_DAY  # type: ignore[attr-defined]
			memo["people"] = people
			memo["shares"] = collection.tile_shares(self.officials_employed(), working_days,
													self.literacy("literacy_elite"), people, days)  # type: ignore[attr-defined]
		return memo["shares"]  # type: ignore[no-any-return]

	def collectible_share(self, tiles: Optional[Iterable[str]] = None) -> float:
		"""The share of what is due on `tiles` (all the state holds when none) that its officials collect."""
		shares = self.collection_shares()
		return collection.collectible_share(shares, self.__dict__["_collection_memo"]["people"], tiles)
