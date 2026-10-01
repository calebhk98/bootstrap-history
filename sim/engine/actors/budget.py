"""A state's standing need: what it keeps up and what that costs this year.

Each line is a thing the state maintains, priced from the physical quantity it
needs: soldiers and officials at the going wage, and the iron an army wears
out at the price the market quotes. The same lines say which people it takes
from the labour pool and which goods it buys, so spending is demand. A line's
`kind` is the claim the state makes on a taxpayer when it cannot pay for the
line: goods in kind (requisition) or service in office.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from .tuning import ADMINISTRATIVE_SPAN, LEVY_RATE_CEILING

# What an army wears out, as a material in the tree's own terms.
EQUIPMENT_MATERIAL = "iron_bar_kg"


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


def army_line(world: Any) -> List[Line]:
	soldiers = world.army_headcount()
	if soldiers <= 0.0:
		return []
	tonnes = soldiers * world.equipment_kg_per_soldier() / 1000.0
	return [Line("army", "requisition", {"labourer": soldiers},
				 soldiers * world.pay_per_person_year("labourer"),
				 {world.commodity_of(EQUIPMENT_MATERIAL): tonnes},
				 world.material_cost(EQUIPMENT_MATERIAL, tonnes))]


def administration_line(world: Any) -> List[Line]:
	officials = world.population_total() * world.state_capacity() / ADMINISTRATIVE_SPAN
	if officials <= 0.0:
		return []
	return [Line("administration", "office", {"scribe": officials},
				 officials * world.pay_per_person_year("scribe"))]


def standing_lines(world: Any) -> List[Line]:
	"""Everything the state keeps up this year, in a fixed order."""
	return army_line(world) + administration_line(world)


def funded_share(need: float, available: float) -> float:
	"""Share of the need that can be paid: all of it while the purse covers it,
	otherwise every line is cut by the same share and nothing is borrowed."""
	if need <= 0.0 or available >= need:
		return 1.0
	return max(0.0, available) / need


def levy_rates(unfunded: Dict[str, float], kinds: Dict[str, str], visible_income: float) -> Tuple[float, float]:
	"""(requisition, office) share of income at full notice that raises the unfunded need
	from the income the state can see. One rate for everyone it sees, never above the
	ceiling; when nothing is visible the state asks the ceiling of whatever turns up."""
	total = sum(unfunded.values())
	if total <= 0.0:
		return 0.0, 0.0
	rate = LEVY_RATE_CEILING if visible_income <= 0.0 else min(LEVY_RATE_CEILING, total / visible_income)
	requisition = sum(amount for name, amount in unfunded.items() if kinds.get(name) == "requisition")
	return rate * requisition / total, rate * (total - requisition) / total
