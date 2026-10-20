"""A state's own plants in use: open them, run them each year, and put their goods to the state's use or the market."""
from typing import Any

from . import state_enterprises


class EnterpriseMixin:
	"""Mixed into `Government`."""

	def run_enterprises(self, world: Any) -> float:
		state_enterprises.open_enterprises(self, world)
		return state_enterprises.run(self, world)

	def input_share(self, entry_key: str, size: float, world: Any) -> float:
		return state_enterprises.input_share(self, entry_key, size, world)

	def sell_output(self, world: Any) -> None:
		state_enterprises.sell(self, world)
