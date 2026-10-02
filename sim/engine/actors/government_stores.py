"""A state's revenue and the goods it holds.

Each form of revenue is assessed on its base (revenue.py). What is paid in coin is credited to the purse;
what is paid in kind (a share of the harvest) enters the stores as tonnes. The lines the state keeps up
draw on the stores before they buy at the market, and what the stores hold beyond a year of what the
lines draw is sold into the goods market at the price it quotes.

TEMPORARY HEURISTIC (CLAUDE.md 4.4): the stores keep one year of what the lines draw and do not spoil;
a granary model with spoilage and a state's own reserve policy would replace both.
"""
import dataclasses
from typing import Any, List

from .budget_line import Line


class StoresMixin:
	"""Mixed into `Government`."""

	def receive_revenue(self, world: Any) -> None:
		"""Take this year's revenue: coin into the purse, goods into the stores, and note both by form."""
		record = self.record  # type: ignore[attr-defined]
		assessments = world.revenue_assessments()
		record.revenue_by_form = {assessed.form: assessed.money for assessed in assessments}
		record.revenue_in_kind = {assessed.form: assessed.money for assessed in assessments if assessed.in_kind}
		record.in_kind_received = {}
		for assessed in assessments:
			if assessed.in_kind:
				record.in_kind_received[assessed.material] = record.in_kind_received.get(assessed.material, 0.0) + assessed.tonnes
				record.stores[assessed.material] = record.stores.get(assessed.material, 0.0) + assessed.tonnes
		self.credit(sum(assessed.money for assessed in assessments if not assessed.in_kind), "taxation")  # type: ignore[attr-defined]

	def draw_stores(self, lines: List[Line], world: Any) -> List[Line]:
		"""The lines as they stand once the stores have supplied what they can of each good; what is
		drawn leaves the stores, and the line buys only the rest."""
		stores = self.record.stores  # type: ignore[attr-defined]
		drawn_lines = []
		for line in lines:
			materials, cost = dict(line.materials), line.material_cost
			price_per_tonne = line.material_cost / sum(line.materials.values()) if line.materials else 0.0
			for material in sorted(stores):
				commodity = world.commodity_of(material)
				wanted = materials.get(commodity, 0.0)
				take = min(stores[material], wanted)
				if take > 0.0:
					cost -= price_per_tonne * take
					materials[commodity] = wanted - take
					stores[material] -= take
			drawn_lines.append(dataclasses.replace(line, materials={c: t for c, t in materials.items() if t > 0.0},
												   material_cost=max(0.0, cost)))
		return drawn_lines

	def sell_surplus(self, lines: List[Line], world: Any) -> None:
		"""Sell what the stores hold beyond what the lines will draw next year, at the market's price."""
		stores = self.record.stores  # type: ignore[attr-defined]
		for material in sorted(stores):
			commodity = world.commodity_of(material)
			keep = sum(line.materials.get(commodity, 0.0) for line in lines)
			surplus = stores[material] - keep
			if surplus > 0.0:
				stores[material] = keep
				world.market_sale(self.actor_id, material, surplus)  # type: ignore[attr-defined]
				self.credit(surplus * world.material_price(material), "sale of stores")  # type: ignore[attr-defined]
		self.record.stores = {material: tonnes for material, tonnes in stores.items() if tonnes > 0.0}  # type: ignore[attr-defined]
