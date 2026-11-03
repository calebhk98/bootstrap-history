"""What actors may ask of the seats: let staff go, read a seat's yearly margin, and the seat's own business review."""
from typing import Any, Dict

from sim.workforce.api import ReleaseStaff


class Seats:
	"""A seat is a business whose staff can leave and whose margin shareholders are paid from. `world` is the root that hands out the parts."""

	# the year plants shut by a review are dated; the scenario's year when None
	review_year: Any = None

	def __init__(self, world: Any) -> None:
		self.world = world

	@property
	def needs(self) -> Any:
		return self.world.needs

	def release_seat_staff(self, seat_id: str, trade: str, people: float) -> None:
		"""`people` of a trade leave a seat's payroll; they go back to the pool the labour market draws on."""
		self.needs.send(ReleaseStaff(seat_id, trade, people))

	def seat_margin(self, seat_id: str) -> float:
		"""What a seat's concerns earned over their upkeep in a year at its present state (not below nothing)."""
		needs = self.needs
		with needs.act_as(seat_id):
			return max(0.0, float(needs.revenue_estimate()) - float(needs.upkeep()))

	def seat_margins(self) -> Dict[str, float]:
		"""Every seat's yearly margin, by seat id."""
		return {seat_id: self.seat_margin(seat_id) for seat_id in self.needs.seat_list()["joined"]}

	def seat_parties(self) -> Any:
		"""Every seat as an actor, by seat id: the founder and other players hold patents and shares."""
		return self.world.seat_book.seat_parties()

	def founder_review(self) -> Any:
		"""The seat's answers to a business review (sim/agents/business_review.py)."""
		return self.needs.seat_review(self.world, self.review_year)
