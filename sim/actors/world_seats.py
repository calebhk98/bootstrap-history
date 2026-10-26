"""What actors may ask of the seats: let staff go, and read a seat's yearly margin."""
from typing import Any, Dict

from sim.workforce.api import ReleaseStaff


class SeatView:
	"""Mixed into `ActorWorld`: a seat is a business whose staff can leave and whose margin shareholders are paid from."""

	needs: Any

	def release_seat_staff(self, seat_id: str, trade: str, people: float) -> None:
		"""`people` of a trade leave a seat's payroll; they go back to the pool the labour market draws on."""
		self.needs.send(ReleaseStaff(seat_id, trade, people))

	def seat_margin(self, seat_id: str) -> float:
		"""What a seat's concerns earned over their upkeep in a year at its present state (not below nothing)."""
		needs = self.needs
		with needs.legacy_act_as(seat_id):
			return max(0.0, float(needs.revenue_estimate()) - float(needs.upkeep()))

	def seat_margins(self) -> Dict[str, float]:
		"""Every seat's yearly margin, by seat id."""
		return {seat_id: self.seat_margin(seat_id) for seat_id in self.needs.legacy_seats()}
