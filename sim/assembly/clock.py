"""Version counters: an owner bumps a channel when it changes state, and a view is fresh while its counters stand still.

One epoch counts every bump and every change of acting seat, so a view that has already checked its signature in the
current epoch answers with one comparison."""
from typing import Dict, Optional, Tuple


class Clock:
	def __init__(self, shadow_every: int = 0):
		self.epoch = 0
		self.era = 0                                  # moves when every cached view must recompute (a load)
		self.acting_seat: Optional[str] = None
		self.shadow_every = shadow_every              # recompute every Nth cached read and compare; 0 turns it off
		self._world: Dict[Tuple[str, str], int] = {}
		self._seat: Dict[Tuple[str, str, Optional[str]], int] = {}
		self._replaced: Dict[str, int] = {}           # seat id -> times a seat under that id was put there whole (a handover, a new seat)

	def bump(self, module_id: str, channel: str) -> None:
		key = (module_id, channel)
		self._world[key] = self._world.get(key, 0) + 1
		self.epoch += 1

	def bump_seat(self, module_id: str, channel: str, seat_id: Optional[str] = None) -> None:
		key = (module_id, channel, self.acting_seat if seat_id is None else seat_id)
		self._seat[key] = self._seat.get(key, 0) + 1
		self.epoch += 1

	def seat_replaced(self, seat_id: str) -> None:
		"""The state under `seat_id` is another seat's now: what was cached for that seat recomputes."""
		self._replaced[seat_id] = self._replaced.get(seat_id, 0) + 1
		self.epoch += 1

	def act_as(self, seat_id: Optional[str]) -> None:
		if seat_id != self.acting_seat:
			self.acting_seat = seat_id
			self.epoch += 1

	def bump_everything(self) -> None:
		"""After a load or any change the owners did not see: every cached view recomputes."""
		self.era += 1
		self.epoch += 1

	def counter(self, module_id: str, channel: str, seat_scoped: bool) -> Tuple[int, int]:
		world = self._world.get((module_id, channel), 0)
		if not seat_scoped:
			return (world, 0)
		return (world, self._seat.get((module_id, channel, self.acting_seat), 0))

	def replaced(self, seat_id: Optional[str]) -> int:
		"""How many times the state under `seat_id` was put there whole (`seat_replaced`)."""
		return self._replaced.get(seat_id, 0)
