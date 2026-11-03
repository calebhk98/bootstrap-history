"""What a state asks the simulated world when it assesses revenue: its declared forms and the bases they read."""
from typing import Any, Dict, FrozenSet, List, Optional, Tuple

from sim.agents.api import government_levers, observed_incomes, revenue
from sim.geography.api import arable_hectares, territory, tiles_held
from sim.labour.api import wage_provider
from sim.reporting.api import output_rules

from .world_memo import once


class Revenue:
	"""Read-only questions behind a state's revenue. `world` is the root that hands out the parts."""

	def __init__(self, world: Any) -> None:
		self.world = world
		self._memo: Dict[str, Any] = {}

	@property
	def needs(self) -> Any:
		return self.world.needs

	def territory(self) -> Any:
		"""Frontier, coast and road length of the tiles the state holds."""
		return territory.holdings(self.needs.home_tiles_held())

	def revenue_forms(self) -> List[Dict[str, Any]]:
		"""The forms of revenue the civilisation's state raises, as its data declares them."""
		return government_levers.revenue_forms(self.world.setting.government().record)

	def fugitive_share(self) -> float:
		"""Share of the country's people who are away, having fled the state's take (the economy's fugitives, by tile)."""
		away = self.needs.agent_fugitive_share_by_tile()
		people = self.world.collection.collection_people_by_tile()
		total = sum(people.values())
		return sum(count * away.get(tile, 0.0) for tile, count in people.items()) / total if total > 0.0 else 0.0

	def revenue_assessments(self) -> List[revenue.Assessment]:
		return once(self._memo, "assessments", lambda: revenue.assess(self.world))  # type: ignore[no-any-return]

	def state_revenue(self) -> float:
		"""Money's worth of what the declared forms yield this year, coin and goods taken in kind alike."""
		return sum(assessment.money for assessment in self.revenue_assessments())

	def society_output(self) -> float:
		"""Yearly value of what the society's market sells: quantities this year at the opening's prices
		(sim/reporting/output.py), in this civilisation's money."""
		def compute() -> float:
			producing = output_rules.share_producing(self.needs.working_age(), self.world.army.soldiers_under_arms())
			return self.needs.economy_output_value() * producing
		return once(self._memo, "output", compute)  # type: ignore[no-any-return]

	def harvest_tonnes(self) -> float:
		"""Tonnes of the staple the economy's producers made last year. Before the economy's first year, TEMPORARY
		HEURISTIC (CLAUDE.md 4.4; retire: Complaint 964): the people are taken to have harvested what they eat."""
		tonnes = self.output_tonnes(wage_provider.staple_material(self.needs.civilisation()))
		return tonnes if tonnes > 0.0 else self.needs.farm_food_demand_kg() / 1000.0

	def output_tonnes(self, material: str, tiles: Optional[FrozenSet[str]] = None) -> float:
		"""Tonnes of a material the producers on the state's tiles (only `tiles` when given) made last year."""
		held = set(self.held_tiles()) if tiles is None else set(tiles)
		by_tile = self.needs.agent_output_tonnes_by_tile()
		return sum(row.get(material, 0.0) for tile, row in by_tile.items() if tile in held)

	def trade_value(self, direction: str) -> float:
		"""Money's worth of goods imported ("in") or exported ("out") in the last completed year."""
		trade = self.needs.trade_value_in_year(self.world.setting.year - 1)
		return float(trade.get(direction, 0.0))

	def coin_stock_value(self) -> float:
		"""Money's worth of the coin this society holds, from its coin standard."""
		return self.needs.coin_stock_value()

	def coin_regime(self) -> str:
		"""The civilisation's coin standard: struck coin, weighed metal, a commodity or fiat."""
		return str((self.needs.civilisation().get("coin_standard") or {}).get("regime", ""))

	def held_tiles(self) -> List[str]:
		return tiles_held(self.needs.civilisation())

	def arable_share(self, tiles: FrozenSet[str]) -> float:
		"""The share of the arable land the state holds that lies on `tiles`."""
		held = self.held_tiles()
		total = sum(arable_hectares(tile) for tile in held)
		return sum(arable_hectares(tile) for tile in held if tile in tiles) / total if total > 0.0 else 0.0

	def land_rent_paid_by_tile(self) -> Dict[str, float]:
		return self.needs.agent_land_rent_paid_by_tile()

	def land_rent_owners(self, tiles: Optional[FrozenSet[str]] = None) -> List[Tuple[Any, float]]:
		"""(stratum, rent received) of the rent paid on `tiles` (all when none): the agent economy keeps rent with its
		household cohorts by what each owns, and the strata are slices of the cohorts ranked by income, so each
		stratum received the rent of its slice. Empty while the economy opens, when the tax is drawn from the edge."""
		curve = self.needs.agent_cohort_land_rents(tiles)
		if not curve:
			return []
		home = [actor for actor in self.world.registry.of_kind("stratum")
				if actor.record.country is None and actor.record.exited_year is None]
		received = observed_incomes(home, self.world, curve)
		return [(stratum, received[stratum.record.stratum]) for stratum in home if received.get(stratum.record.stratum, 0.0) > 0.0]
