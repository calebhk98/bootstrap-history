"""One thing a state keeps up and what it costs this year."""
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Line:
	name: str
	kind: str  # "requisition" or "office"
	labour: Dict[str, float] = field(default_factory=dict)  # trade -> people kept
	wages: float = 0.0
	materials: Dict[str, float] = field(default_factory=dict)  # commodity -> tonnes a year
	material_cost: float = 0.0

	@property
	def money(self) -> float:
		return self.wages + self.material_cost
