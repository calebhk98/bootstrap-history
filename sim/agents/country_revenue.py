"""What a country's own state reads when it assesses revenue: its declared forms and their bases, from its profile and its
own part of the economy, so the one `Government` actor runs a foreign country by the same rules as the home one
(revenue.py, budget.py) over the country's figures.

A reading the country's own part of the economy keeps no record of is a refusal (`NoCountryEconomy`, naming the country) or
None, never the home figure.
"""
from typing import Any, Dict, FrozenSet, List, Optional, Tuple

from sim.geography.api import arable_hectares, territory

from . import government_levers, revenue, strata_observed
from .country_part import SharedPart
from .no_country_economy import NoCountryEconomy


class CountryRevenue(SharedPart):
	"""The country's revenue forms and their bases."""

	part = "revenue"

	def __init__(self, world: Any) -> None:
		super().__init__(world)
		self._assessed: Optional[List[revenue.Assessment]] = None   # this year's assessments

	def revenue_forms(self) -> List[Dict[str, Any]]:
		"""The forms of revenue the country's state raises, as its civilisation file declares them."""
		return government_levers.revenue_forms(self.world.setting.government().record)

	def revenue_assessments(self) -> List[revenue.Assessment]:
		"""Every declared form assessed on this year's base; kept for the year this scope lives."""
		if self._assessed is None:
			self._assessed = revenue.assess(self.world)
		return self._assessed

	def state_revenue(self) -> float:
		return sum(assessment.money for assessment in self.revenue_assessments())

	def harvest_tonnes(self) -> float:
		"""Grain the country's farm harvested last year (none before its first)."""
		return float(self.world.profile.farm.get("harvest_kg", 0.0)) / 1000.0

	def held_tiles(self) -> List[str]:
		return list(self.world.profile.home_tiles)

	def territory(self) -> Any:
		"""Frontier, coast and road length of the tiles the country holds."""
		return territory.holdings(self.held_tiles())

	def arable_share(self, tiles: FrozenSet[str]) -> float:
		"""The share of the arable land the country holds that lies on `tiles`."""
		held = self.held_tiles()
		total = sum(arable_hectares(tile) for tile in held)
		return sum(arable_hectares(tile) for tile in held if tile in tiles) / total if total > 0.0 else 0.0

	def output_tonnes(self, material: str, tiles: Optional[FrozenSet[str]] = None) -> float:
		"""What the producers on the country's tiles (only `tiles` of them when given) made of a material last year."""
		held = frozenset(self.held_tiles())
		return self.shared.output_tonnes(material, held if tiles is None else held & frozenset(tiles))

	def land_rent_paid_by_tile(self) -> Dict[str, float]:
		held = set(self.held_tiles())
		return {tile: rent for tile, rent in self.shared.land_rent_paid_by_tile().items() if tile in held}

	def land_rent_owners(self, tiles: Optional[FrozenSet[str]] = None) -> List[Tuple[Any, float]]:
		"""(stratum, rent received) of the rent paid on the country's `tiles` (all it holds when none): its own cohorts
		keep the rent by what each owns, and its strata are slices of those cohorts ranked by income. Nobody while its
		economy keeps no cohorts, when the tax is drawn from the edge."""
		held = frozenset(self.held_tiles())
		try:
			curve = self.world.own.get().land_rent_curve(held if tiles is None else held & frozenset(tiles))
		except NoCountryEconomy:
			return []
		strata = [stratum for stratum in self.world.people.country_strata() if stratum.record.exited_year is None]
		received = strata_observed.observed_incomes(strata, self.world, curve) if curve else {}
		return [(stratum, received[stratum.record.stratum]) for stratum in strata if received.get(stratum.record.stratum, 0.0) > 0.0]

	def trade_value(self, direction: str) -> float:
		"""Money's worth of the goods that crossed the country's border last year, as its own part of the economy
		recorded them (imports where they landed, exports where they left)."""
		return float(self.world.own.get().trade_value(direction))

	def coin_stock_value(self) -> float:
		"""Money's worth of the metal in the money the country's own people and producers hold."""
		return float(self.world.own.get().coin_stock_value())

	def coin_regime(self) -> str:
		"""The standard of the money the country's economy uses."""
		return str(self.world.own.get().coin_regime())

	def society_output(self) -> float:
		"""What this country's producers make at its prices."""
		own = self.world.own
		return own.answer("output", own.get().society_output())
