"""The yearly review of a business: which plants close, and why, the same rules for every owner.

A plant closes for one of a few reasons: its owner is short of the people to run it (`STAFF_SHORT`), it has lost
money for too many years running or the owner must cut its losses now (`LOSS_MAKING`), or the owner's creditors take
it (`CREDITOR_SEIZURE`). The business decides which; the owner says how it shuts a plant (a firm forgets it, the
founder's seat mothballs it) through the hooks of `Reviewable`.
"""
from typing import TYPE_CHECKING, Any, List, NamedTuple, Sequence

from .business_plant import OPERATING, Plant
from .tuning import EXIT_LOSS_YEARS

if TYPE_CHECKING:
	from .business import Business

STAFF_SHORT = "staff"
LOSS_MAKING = "loss_making"
CREDITOR_SEIZURE = "creditor_seizure"
ALL_RULES = (STAFF_SHORT, LOSS_MAKING, CREDITOR_SEIZURE)


class Closure(NamedTuple):
	entry_key: str
	reason: str


class Reviewable:
	"""What an owner answers when its business is reviewed. The defaults suit an owner with no staffing pool, no
	creditors at the door and no plants it keeps for other reasons than their takings (a firm)."""

	def staff_closures(self, world: Any) -> List[str]:
		"""The plants a real shortage of people forces shut, in the order they close."""
		return []

	def reopens_staffed_plant(self, entry_key: str, world: Any) -> bool:
		"""Try to bring a plant shut for want of staff back; whether it is running again."""
		return False

	def reopening_order(self, entry_keys: Sequence[str], world: Any) -> List[str]:
		return sorted(entry_keys)

	def sheds_losses(self, world: Any) -> bool:
		"""Whether the owner lets plants be shut for losing money (the founder's `auto_shed` policy)."""
		return True

	def cuts_losses_now(self, world: Any) -> bool:
		"""Whether the owner's books force it to shut loss-makers this year, whatever their record."""
		return False

	def spares_plant(self, entry_key: str, world: Any) -> bool:
		"""Whether the plant is held whatever it loses or owes (the goal needs it, or it is not the owner's to shut)."""
		return False

	def serves_beyond_takings(self, entry_key: str, world: Any) -> bool:
		"""Whether the plant is worth running at a loss, for what it gives the owner other than takings: not shut for
		a run of loss years, and the last to go when losses must be cut."""
		return False

	def standing_margin(self, entry_key: str, world: Any) -> float:
		"""What the plant makes in a year at today's figures, to rank it and to tell a loss-maker."""
		plant = self.business.plant_of(entry_key)  # type: ignore[attr-defined]
		return 0.0 if plant is None or plant.margin is None else plant.margin

	def creditors_press(self, world: Any) -> bool:
		"""Whether what the owner owes is past what lenders will carry, so they take what they can."""
		return False

	def shut(self, entry_key: str, reason: str, world: Any) -> None:
		"""Close the plant; a firm forgets it."""
		self.business.close_plant(entry_key)  # type: ignore[attr-defined]

	def proceeds_of_seizure(self, entry_key: str, world: Any) -> float:
		"""What the creditors' taking of the plant repays."""
		return 0.0

	def receive_seizure(self, entry_key: str, proceeds: float, world: Any) -> None:
		"""Credit the proceeds of a seized plant to the owner's debt."""


def _operating(business: "Business") -> List[Plant]:
	return [plant for plant in business.plants if plant.state == OPERATING]


def _close(business: "Business", owner: Any, world: Any, entry_key: str, reason: str, closed: List[Closure]) -> None:
	owner.shut(entry_key, reason, world)
	closed.append(Closure(entry_key, reason))


def review(business: "Business", owner: Any, world: Any, rules: Sequence[str] = ALL_RULES) -> List[Closure]:
	"""Shut the plants the named rules close, in the order the rules are listed here. Returns what closed and why."""
	closed: List[Closure] = []
	if STAFF_SHORT in rules:
		for entry_key in owner.staff_closures(world):
			_close(business, owner, world, entry_key, STAFF_SHORT, closed)
	if LOSS_MAKING in rules and owner.sheds_losses(world):
		_shed_losses(business, owner, world, closed)
	if CREDITOR_SEIZURE in rules:
		_seize(business, owner, world, closed)
	return closed


def _shed_losses(business: "Business", owner: Any, world: Any, closed: List[Closure]) -> None:
	for plant in _operating(business):
		if (plant.loss_years >= EXIT_LOSS_YEARS and not owner.spares_plant(plant.entry_key, world)
				and not owner.serves_beyond_takings(plant.entry_key, world)):
			_close(business, owner, world, plant.entry_key, LOSS_MAKING, closed)
	while owner.cuts_losses_now(world):
		worst = _worst_loss_maker(business, owner, world)
		if worst is None:
			break
		_close(business, owner, world, worst, LOSS_MAKING, closed)


def _worst_loss_maker(business: "Business", owner: Any, world: Any) -> Any:
	"""The operating plant that loses most, those worth running at a loss last; None when none loses money."""
	losing = [plant.entry_key for plant in _operating(business)
			  if owner.standing_margin(plant.entry_key, world) < 0.0 and not owner.spares_plant(plant.entry_key, world)]
	if not losing:
		return None
	return min(losing, key=lambda entry_key: (owner.serves_beyond_takings(entry_key, world),
											  owner.standing_margin(entry_key, world), entry_key))


def _seize(business: "Business", owner: Any, world: Any, closed: List[Closure]) -> None:
	"""While the owner's creditors press, they take the worst loss-making plant and its proceeds repay them."""
	while owner.creditors_press(world):
		worst = _worst_loss_maker(business, owner, world)
		if worst is None:
			break
		owner.receive_seizure(worst, owner.proceeds_of_seizure(worst, world), world)
		_close(business, owner, world, worst, CREDITOR_SEIZURE, closed)


def reopen(business: "Business", owner: Any, world: Any) -> List[str]:
	"""Bring back the plants shut for want of staff that the owner can staff again, the first in its order first."""
	shut = [plant.entry_key for plant in business.plants if plant.state != OPERATING and plant.reason == STAFF_SHORT]
	return [entry_key for entry_key in owner.reopening_order(shut, world) if owner.reopens_staffed_plant(entry_key, world)]
