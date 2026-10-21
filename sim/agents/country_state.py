"""What a country's own state reads: its revenue forms and their bases, its people, land and holdings, its army,
its payroll and its purchases. `CountryWorld` mixes this in, so the one `Government` actor runs a foreign country
by the same rules as the home one (revenue.py, budget.py) over the country's figures.

A reading the world keeps for the home country alone (no trade book, no interest groups) is
answered with nothing here, never with the home figure; Complaint 647 lists them.
"""
import functools
from typing import Any, Dict, FrozenSet, List, Optional, Tuple

from sim.geography.api import arable_hectares, settlement, territory, usable_modes
from sim.world import demography

from . import collection, government_levers, ledger, revenue
from .collection_world import CollectionView
from .edges import EDGE_STATE_SPENDING, EDGE_WORKERS
from .payroll import share_out
from .tuning_spending import THREAT_ARMY_RESPONSE
from .tuning_country import ARMY_SHARE_OF_POPULATION

# the keys of a civilisation's data a country's state reads
HAZARDS_KEY = "hazards"
STANDING_ARMY_KEY = "standing_army"


@functools.lru_cache(maxsize=64)
def working_age_of_stationary(population: float) -> float:
	"""Working-age people among `population` in the model's stable age structure (before a country's Population has stepped)."""
	return demography.Population.stationary(population, seed=0).working_age if population > 0.0 else 0.0


class CountryStateView(CollectionView):
	"""The state-facing readings of `CountryWorld`; `profile`, `_shared` and `_holder` are its."""

	profile: Any
	_shared: Any
	_holder: Any

	# ---- revenue
	def revenue_forms(self) -> List[Dict[str, Any]]:
		"""The forms of revenue the country's state raises, as its civilisation file declares them."""
		return government_levers.revenue_forms(self.government().record)

	def revenue_assessments(self) -> List[revenue.Assessment]:
		"""Every declared form assessed on this year's base; kept for the year this scope lives."""
		if getattr(self, "_assessed", None) is None:
			self._assessed = revenue.assess(self)
		return self._assessed

	def state_revenue(self) -> float:
		return sum(assessment.money for assessment in self.revenue_assessments())

	def harvest_tonnes(self) -> float:
		"""Grain the country's farm harvested last year (none before its first)."""
		return float(self.profile.farm.get("harvest_kg", 0.0)) / 1000.0

	def held_tiles(self) -> List[str]:
		return list(self.profile.home_tiles)

	def collection_people_by_tile(self) -> Dict[str, float]:
		"""The country's people spread over its tiles by settlement."""
		return collection.spread_people(self.population_total(), settlement.population_shares(self.held_tiles()))

	def collection_modes(self) -> List[str]:
		"""The route modes the country's starting technologies open."""
		return usable_modes([self.baseline_knowledge()])

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
		return self._shared.output_tonnes(material, held if tiles is None else held & frozenset(tiles))

	def land_rent_paid_by_tile(self) -> Dict[str, float]:
		held = set(self.held_tiles())
		return {tile: rent for tile, rent in self._shared.land_rent_paid_by_tile().items() if tile in held}

	def land_rent_owners(self, tiles: Optional[FrozenSet[str]] = None) -> List[Tuple[Any, float]]:
		"""Nobody is named: the rent a country's tiles pay is drawn from the edge (retire: Complaint 647)."""
		return []

	def trade_value(self, direction: str) -> float:
		"""No country keeps a trade book of its own yet (Complaint 647)."""
		return 0.0

	def coin_stock_value(self) -> float:
		"""Money's worth of the metal in the money the country's own people and producers hold."""
		return float(self._own_economy().coin_stock_value())

	def coin_regime(self) -> str:
		"""The standard of the money the country's economy uses."""
		return str(self._own_economy().coin_regime())

	def material_cost(self, material: str, tonnes: float) -> Optional[float]:
		"""Money to buy this many tonnes of a material at the price the country's own markets quote; None when
		they quote none (not on sale)."""
		price = self._own_economy().price_per_tonne(material)
		return None if price is None else price * tonnes

	def material_price(self, material: str) -> float:
		"""Money for one tonne of a material at the country's own quote (nothing when it is not on sale)."""
		return self.material_cost(material, 1.0) or 0.0

	# ---- people and holdings
	def national_people(self, trade: str) -> float:
		"""People of a trade in the country. TEMPORARY HEURISTIC (CLAUDE.md 4.4): no country counts its people by
		trade, so every trade is bounded by the working age, the unskilled labourers' count (retire: Complaint 647)."""
		if self.profile.cohorts:
			return float(self.profile.cohorts.get("working_age", 0.0))
		return working_age_of_stationary(self.profile.population)

	def local_staff(self, trade: str, people: float) -> float:
		"""A country's state staff are its own people, not the founder's labour pool."""
		return 0.0

	# ---- the army
	def threat_pressure(self) -> float:
		"""Probability a year of the country's own declared hazards sack a site."""
		year = self._shared.year
		return sum(float(hazard.get("sack_chance", 0.0)) for hazard in self.profile.extra.get(HAZARDS_KEY, [])
				   if hazard.get("years") and hazard["years"][0] <= year <= hazard["years"][1])

	def army_wanted(self) -> float:
		"""Soldiers the state wants: the force its civilisation declares, else a share of its people, raised by
		the threat its hazards describe."""
		declared = self.profile.extra.get(STANDING_ARMY_KEY)
		opening = float(declared) if declared is not None else self.population_total() * ARMY_SHARE_OF_POPULATION
		return max(0.0, opening * (1.0 + THREAT_ARMY_RESPONSE * self.threat_pressure()))

	def soldiers_under_arms(self) -> float:
		"""Soldiers the state keeps now: what it paid for last year, else the force it wants."""
		kept = self.government().record.army
		return kept if kept > 0.0 else self.army_wanted()

	def fleet_goods(self, holder_id: Optional[str] = None) -> List[Any]:
		return self._shared.fleet_goods(holder_id or self.government().actor_id)

	# ---- taxpayers and the levy
	def patron_ask(self) -> float:
		"""Nobody is the patron of a country's state."""
		return 0.0

	def group_claims(self) -> Dict[str, float]:
		"""Interest groups form around the founder's economy; a country's state owes none yet (Complaint 647)."""
		return {}

	def visible_taxpayers(self) -> List[Tuple[float, float]]:
		"""(visible scale, taxable income) of the firms of the country the state can see."""
		lookup = getattr(self._holder, "active_firms", None)
		firms = lookup() if callable(lookup) else []
		return [(self.visible_scale_of(firm), max(0.0, firm.record.last_margin))
				for firm in firms if firm.record.country == self.profile.country]

	def notice_over(self, scale: float, capacity: Optional[float] = None) -> float:
		return self._shared.notice_over(scale, self.state_reach() if capacity is None else capacity)

	def levy_shares(self, scale: float, protection: float = 0.0, state: Any = None) -> Any:
		"""(requisition, office) shares of income this country's state assesses at a visible scale: its own capacity,
		tax share and the rates its shortfall set last year."""
		requisition, office = self.government().levy_rates() if hasattr(self.government(), "levy_rates") else (0.0, 0.0)
		return self._shared.levy_shares(scale, protection, (self.state_reach(), self.tax_share(), requisition, office))

	# ---- credit
	def state_may_borrow(self, state: Any) -> bool:
		"""Whether the state holds a technology declaring the `state_credit` mechanic, in its own knowledge or its country's."""
		return any(state.knows(node_id, self) for node_id in self._shared.nodes_with_mechanic("state_credit"))

	# ---- paying out and buying
	def country_free_strata(self) -> List[Any]:
		return [stratum for stratum in self.country_strata()
				if stratum.record.exited_year is None and not stratum.is_bonded() and stratum.record.members > 0.0]

	def pay_wages(self, payer: Any, amount: float, purpose: Any) -> None:
		"""Pay a country's people: its free strata by their numbers, or the workers' edge while it has none."""
		people = self.country_free_strata()
		if not people:
			ledger.transfer(payer, self.edge(EDGE_WORKERS), amount, purpose)
			return
		share_out(payer, people, [stratum.record.members for stratum in people], amount, purpose)

	def market_purchase(self, buyer_id: str, commodity: str, tonnes: float, budget: float = 0.0) -> None:
		"""A country has no goods market of its own in the book: what its state buys is paid for at once."""
		buyer = getattr(self._holder, "actors", {}).get(buyer_id)
		if buyer is not None and budget > 0.0:
			ledger.transfer(buyer, self.edge(EDGE_STATE_SPENDING), budget, "purchase")

	def market_sale(self, seller_id: str, material: str, tonnes: float, from_concerns: Any = None) -> None:
		"""What a country's state sells is paid for at the price the market quotes."""
		seller = getattr(self._holder, "actors", {}).get(seller_id)
		if seller is not None and tonnes > 0.0:
			ledger.transfer(self.edge(EDGE_STATE_SPENDING), seller, self.material_cost(material, tonnes) or 0.0, "sale")
