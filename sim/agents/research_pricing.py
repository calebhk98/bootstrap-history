"""What pioneering a node costs in a country: its materials at the country's quotes, its capital at the country's price level
and its hours at the country's pay. Plain functions of plain values (the country's part reads the figures)."""
from typing import Callable, Mapping, Optional


def materials_at_quotes(material_tonnes: Mapping[str, float], material_cost: Callable[[str, float], Optional[float]]) -> Optional[float]:
	"""Money for the tonnes of each material at the quotes `material_cost` gives; None when any of them is quoted nowhere."""
	total = 0.0
	for material in sorted(material_tonnes):
		cost = material_cost(material, material_tonnes[material])
		if cost is None:
			return None
		total += cost
	return total


def hours_at_pay(hours: Mapping[str, float], hourly_pay: Callable[[str], float]) -> float:
	"""Money for the hours of each trade at the pay `hourly_pay` gives."""
	return sum(amount * hourly_pay(trade) for trade, amount in sorted(hours.items()))


def cost_at_country_prices(capital: float, price_index: float, materials_cost: Optional[float], labour_cost: float) -> Optional[float]:
	"""The node's cost in the country: its book capital at the country's price level, plus its materials and labour as
	priced there; None when a material is quoted nowhere in the country."""
	if materials_cost is None:
		return None
	return capital * price_index + materials_cost + labour_cost
