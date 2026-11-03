"""How the founder's household answers a business review: each hook asks the world for the seat's answer."""
from typing import Any, List, Sequence

from .business_review import Reviewable


class FounderReview(Reviewable):
	"""The founder's seat as the owner of a business under review."""

	def staff_closures(self, world: Any) -> List[str]:
		return world.seats.founder_review().staff_closures()

	def reopens_staffed_plant(self, entry_key: str, world: Any) -> bool:
		return world.seats.founder_review().reopens_staffed_plant(entry_key)

	def reopening_order(self, entry_keys: Sequence[str], world: Any) -> List[str]:
		return world.seats.founder_review().reopening_order(entry_keys)

	def sheds_losses(self, world: Any) -> bool:
		return world.seats.founder_review().sheds_losses()

	def cuts_losses_now(self, world: Any) -> bool:
		return world.seats.founder_review().cuts_losses_now()

	def spares_plant(self, entry_key: str, world: Any) -> bool:
		return world.seats.founder_review().spares_plant(entry_key)

	def serves_beyond_takings(self, entry_key: str, world: Any) -> bool:
		return world.seats.founder_review().serves_beyond_takings(entry_key)

	def standing_margin(self, entry_key: str, world: Any) -> float:
		return world.seats.founder_review().standing_margin(entry_key)

	def creditors_press(self, world: Any) -> bool:
		return world.seats.founder_review().creditors_press()

	def shut(self, entry_key: str, reason: str, world: Any) -> None:
		world.seats.founder_review().shut(entry_key, reason)

	def proceeds_of_seizure(self, entry_key: str, world: Any) -> float:
		return world.seats.founder_review().proceeds_of_seizure(entry_key)

	def receive_seizure(self, entry_key: str, proceeds: float, world: Any) -> None:
		world.seats.founder_review().receive_seizure(entry_key, proceeds)
