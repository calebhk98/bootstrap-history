"""One thing a state keeps up and what it costs this year."""
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class Line:
	name: str
	kind: str  # "requisition" or "office"
	labour: Dict[str, float] = field(default_factory=dict)  # trade -> people kept
	wages: float = 0.0
	materials: Dict[str, float] = field(default_factory=dict)  # commodity -> tonnes a year
	material_cost: float = 0.0
	transfer: float = 0.0  # money handed to someone outside the state's own service
	unbuyable: Dict[str, float] = field(default_factory=dict)  # commodity -> tonnes a year no market sells: needed, unmet

	@property
	def money(self) -> float:
		return self.wages + self.material_cost + self.transfer


def goods(world: Any, material: str, tonnes: float) -> Dict[str, Any]:
	"""The goods fields of a line that needs `tonnes` of a material: bought at the market's price when it is on sale,
	otherwise unbuyable (needed, not bought, costing nothing)."""
	commodity = world.commodity_of(material)
	cost = world.material_cost(material, tonnes)
	if cost is None:
		return {"unbuyable": {commodity: tonnes}}
	return {"materials": {commodity: tonnes}, "material_cost": cost}
