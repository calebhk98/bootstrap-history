"""The grain a state holds against a bad harvest.

The reserve is a target in years of the town dwellers' subsistence grain. Stored grain spoils a share a year; grain
above the target, or any of it while the market quote is far above what the state takes as normal, is sold into
the goods market; below the target the state buys when the quote is below normal, out of a surplus.
"""
from typing import Any

from .tuning_spending import (GRANARY_LOSS_SHARE_PER_YEAR, GRANARY_PRICE_MEMORY, GRANARY_RELEASE_PRICE_PREMIUM,
							  GRANARY_RELEASE_SHARE, GRANARY_RESERVE_YEARS_OF_URBAN_FOOD)


class Granary:
	"""A state's grain reserve, on the government that owns the stores."""

	def __init__(self, government: Any) -> None:
		self.government = government

	def granary_target(self, world: Any) -> float:
		"""Tonnes of grain the state wants in store."""
		return (GRANARY_RESERVE_YEARS_OF_URBAN_FOOD * world.people.urban_population()
				* world.people.subsistence_kg_per_person_year() / 1000.0)

	def keep_granary(self, world: Any) -> float:
		"""Spoil, then sell what is above the target or what a dear market calls for; the tonnes sold."""
		record = self.government.record
		staple = world.quotes.staple_material()
		stored = record.stores.get(staple, 0.0) * (1.0 - GRANARY_LOSS_SHARE_PER_YEAR)
		price = world.quotes.material_price(staple)
		normal = record.grain_price_reference if record.grain_price_reference > 0.0 else price
		sell = max(0.0, stored - self.granary_target(world))
		if price > normal * (1.0 + GRANARY_RELEASE_PRICE_PREMIUM):
			sell = max(sell, GRANARY_RELEASE_SHARE * stored)
		if sell > 0.0:
			world.market.market_sale(self.government.actor_id, staple, sell)
		record.stores[staple] = stored - sell
		record.grain_price_reference = normal + GRANARY_PRICE_MEMORY * (price - normal)
		return sell

	def restock_granary(self, excess: float, world: Any) -> float:
		"""Bid for grain up to the target when the quote is below normal, with at most `excess`; the money bid.
		TEMPORARY HEURISTIC (CLAUDE.md 4.4): the bid is taken as filled, as the market does not report what a
		state's bid bought."""
		record = self.government.record
		staple = world.quotes.staple_material()
		shortfall = self.granary_target(world) - record.stores.get(staple, 0.0)
		if excess <= 0.0 or shortfall <= 0.0 or world.quotes.material_price(staple) >= record.grain_price_reference:
			return 0.0
		cost = world.quotes.material_cost(staple, shortfall)
		if cost is None or cost <= 0.0:
			return 0.0
		bought = min(1.0, excess / cost)
		world.market.market_purchase(self.government.actor_id, world.quotes.commodity_of(staple), shortfall * bought, cost * bought)
		record.stores[staple] = record.stores.get(staple, 0.0) + shortfall * bought
		return cost * bought
