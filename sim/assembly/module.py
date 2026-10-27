"""The base every module implementation derives from: its id, what it was handed, and how it says its state changed."""
from typing import Any, Callable, Dict, Optional

from .clock import Clock


class Module:
	"""Set up by the assembly before `setup()` runs: `module_id`, `needs` (the views, points and `send` it declared),
	`clock`, and `world` / `seat` (its own saved state, rebound on a load and on every seat switch)."""
	module_id: str
	needs: Any
	clock: Clock
	world: Any = None
	seat: Any = None
	kernels: Dict[str, Callable]                           # this module's kernels by name, as bound by the assembly
	seat_slot_of: Optional[Callable[[str], Any]] = None   # set by the engine: another seat's state, by seat id

	def kernel(self, name: str) -> Callable:
		"""The function to call for the kernel `name` this module declared: a mod's replacement, else the reference."""
		return self.kernels[name]

	def seat_of(self, seat_id: str) -> Any:
		"""This module's state for the seat `seat_id`, which need not be the acting one (a command that names a seat)."""
		return self.seat_slot_of(seat_id)

	def setup(self) -> None:
		"""Called once after assembly; override to build what the module keeps between calls (never saved)."""

	def bump(self, channel: str) -> None:
		self.clock.bump(self.module_id, channel)

	def bump_seat(self, channel: str, seat_id: Optional[str] = None) -> None:
		self.clock.bump_seat(self.module_id, channel, seat_id)
