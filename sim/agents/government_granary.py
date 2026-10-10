"""The grain a state holds against a bad harvest.

The reserve is a target in years of the town dwellers' subsistence grain. Stored grain spoils a share a year; grain
above the target, or any of it while the market quote is far above what the state takes as normal, is sold into
the goods market; below the target the state buys when the quote is below normal, out of a surplus.
"""
from typing import Any

from .budget_lines import DOLE_MATERIAL
from .tuning_spending import (GRANARY_LOSS_SHARE_PER_YEAR, GRANARY_PRICE_MEMORY, GRANARY_RELEASE_PRICE_PREMIUM,
							  GRANARY_RELEASE_SHARE, GRANARY_RESERVE_YEARS_OF_URBAN_FOOD)


class GranaryMixin:
	"""Mixed into `Government`."""

	def granary_target(self, world: Any) -> float:
		"""Tonnes of grain the state wants in store."""
		return (GRANARY_RESERVE_YEARS_OF_URBAN_FOOD * world.urban_population()
				* world.subsistence_kg_per_person_year() / 1000.0)

	def keep_granary(self, world: Any) -> float:
		"""Spoil, then sell what is above the target or what a dear market calls for; the tonnes sold."""
		record = self.record  # type: ignore[attr-defined]
		stored = record.stores.get(DOLE_MATERIAL, 0.0) * (1.0 - GRANARY_LOSS_SHARE_PER_YEAR)
		price = world.material_price(DOLE_MATERIAL)
		normal = record.grain_price_reference if record.grain_price_reference > 0.0 else price
		sell = max(0.0, stored - self.granary_target(world))
		if price > normal * (1.0 + GRANARY_RELEASE_PRICE_PREMIUM):
			sell = max(sell, GRANARY_RELEASE_SHARE * stored)
		if sell > 0.0:
			world.market_sale(self.actor_id, DOLE_MATERIAL, sell)  # type: ignore[attr-defined]
		record.stores[DOLE_MATERIAL] = stored - sell
		record.grain_price_reference = normal + GRANARY_PRICE_MEMORY * (price - normal)
		return sell

	def restock_granary(self, excess: float, world: Any) -> float:
		"""Bid for grain up to the target when the quote is below normal, with at most `excess`; the money bid.
		TEMPORARY HEURISTIC (CLAUDE.md 4.4): the bid is taken as filled, as the market does not report what a
		state's bid bought."""
		record = self.record  # type: ignore[attr-defined]
		shortfall = self.granary_target(world) - record.stores.get(DOLE_MATERIAL, 0.0)
		if excess <= 0.0 or shortfall <= 0.0 or world.material_price(DOLE_MATERIAL) >= record.grain_price_reference:
			return 0.0
		cost = world.material_cost(DOLE_MATERIAL, shortfall)
		if cost <= 0.0:
			return 0.0
		bought = min(1.0, excess / cost)
		world.market_purchase(self.actor_id, world.commodity_of(DOLE_MATERIAL), shortfall * bought, cost * bought)  # type: ignore[attr-defined]
		record.stores[DOLE_MATERIAL] = record.stores.get(DOLE_MATERIAL, 0.0) + shortfall * bought
		return cost * bought
