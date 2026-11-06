"""A state's own plants in use: open them, run them each year, and put their goods to the state's use or the market."""
from typing import Any

from . import state_enterprises


class Enterprises:
	"""A state's own plants, on the government that owns them."""

	def __init__(self, government: Any) -> None:
		self.government = government

	def run_enterprises(self, world: Any) -> float:
		state_enterprises.open_enterprises(self.government, world)
		return state_enterprises.run(self.government, world)

	def input_share(self, entry_key: str, size: float, world: Any) -> float:
		return state_enterprises.input_share(self.government, entry_key, size, world)

	def sell_output(self, world: Any) -> None:
		state_enterprises.sell(self.government, world)
