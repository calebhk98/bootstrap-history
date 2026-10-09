"""What actors may ask of the seats: let staff go, and read a seat's yearly margin."""
from typing import Any, Dict


class SeatView:
	"""Mixed into `SimWorld`: a seat is a business whose staff can leave and whose margin shareholders are paid from."""

	_sim: Any

	def release_seat_staff(self, seat_id: str, trade: str, people: float) -> None:
		"""`people` of a trade leave a seat's payroll; they go back to the pool the labour market draws on."""
		sim = self._sim
		with sim.act_as(seat_id):
			sim.labour.fire(trade, people)

	def seat_margin(self, seat_id: str) -> float:
		"""What a seat's concerns earned over their upkeep in a year at its present state (not below nothing)."""
		sim = self._sim
		with sim.act_as(seat_id):
			return max(0.0, float(sim.revenue()) - float(sim.upkeep()))

	def seat_margins(self) -> Dict[str, float]:
		"""Every seat's yearly margin, by seat id."""
		return {seat_id: self.seat_margin(seat_id) for seat_id in self._sim.state.seats}
