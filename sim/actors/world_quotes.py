"""What the goods market quotes and what the people live on."""
from typing import Any, Optional

from sim.labour.api import wage_provider


class Quotes:
	"""Quotes of materials at the home market. `world` is the root that hands out the parts."""

	def __init__(self, world: Any) -> None:
		self.world = world

	@property
	def needs(self) -> Any:
		return self.world.needs

	def commodity_of(self, material: str) -> str:
		return self.needs.material_commodity[material]

	def material_cost(self, material: str, tonnes: float) -> Optional[float]:
		"""Money to buy this many tonnes of a material at the price the market quotes; None when nothing sells it."""
		quote = self.needs.material_purchase_cost(material, tonnes)
		return None if quote is None else quote[0]

	def material_price(self, material: str) -> float:
		"""Money for one tonne of a material at the price the market quotes."""
		return self.material_cost(material, 1.0) or 0.0

	def staple_material(self) -> str:
		"""The material the civilisation's people live on, from its data."""
		return wage_provider.staple_material(self.needs.civilisation())
