"""What an actor can see and price: a read-only view of the simulated world.

Actors never touch `Sim` directly. They ask this view, which keeps them free
of the engine and lets a test or a second scenario supply another one.
"""
import hashlib
import random
from typing import Any, Dict, List, Optional, Set

from sim.engine.data import TRADES_ABSENT

from . import supply
from .world_budget import BudgetView
from .world_disclosure import DisclosureView
from .world_groups import GroupView
from .tuning import OBSERVATION_RANGE_KM


class SimWorld(BudgetView, GroupView, DisclosureView):
	"""The `Sim`'s answers to the questions actors ask."""

	def __init__(self, sim: Any) -> None:
		self._sim = sim
		# Answers that hold for the whole of one yearly turn.
		self._memo: Dict[str, Any] = {}

	def _once(self, key: str, compute: Any) -> Any:
		if key not in self._memo:
			self._memo[key] = compute()
		return self._memo[key]

	@property
	def year(self) -> int:
		return self._sim.state.scenario.year

	@property
	def nodes(self) -> Dict[str, Any]:
		return self._sim.nodes

	@property
	def civ_id(self) -> str:
		return str(self._sim.civ.get("id"))

	def baseline_knowledge(self) -> Set[str]:
		"""What the society already knows without the founder."""
		return self._once("baseline", lambda: set(self._sim.state.projects.granted))

	def founder_inventions(self) -> List[str]:
		"""Everything the founder has completed that the society did not have."""
		def compute() -> List[str]:
			projects = self._sim.state.projects
			return sorted(projects.done - projects.granted)
		return self._once("inventions", compute)

	def demonstrated(self) -> Set[str]:
		return self._once("demonstrated", lambda: set(self.founder_inventions()))

	def is_public(self, node_id: str) -> bool:
		return node_id in self._sim.state.projects.operating

	def exposure(self, node_id: str, location: Optional[str]) -> float:
		"""How much of an invention an observer at `location` can learn, 0..1."""
		visibility = self.base_visibility(node_id)
		if location is None:
			return visibility
		distance = self._sim.distance_to_tile_km(location)
		return visibility / (1.0 + distance / OBSERVATION_RANGE_KM)

	def state_weights(self) -> Dict[str, float]:
		return self._once("weights", self._sim.state_trait_weights)

	def society_output(self) -> float:
		"""Yearly value of the working population's labour at the unskilled wage: the working
		people not under arms, scaled by what the economy is making at present."""
		sim = self._sim
		def compute() -> float:
			producing = max(0.0, sim.population.working_age - self.soldiers_under_arms())
			return producing * sim.HOURS_PER_PERSON_YEAR * sim.wage_per_hour("labourer") * sim.state.economy.output_factor
		return self._once("output", compute)

	def state_revenue(self) -> float:
		sim = self._sim
		return self._once("revenue", lambda: (
			self.society_output() * float(sim.civ["starting_tax_share"]) * sim.state_capacity))

	def visible_scale_of(self, actor: Any) -> float:
		"""How large and visible any actor looks to the state: its staff, its wealth and its prominence."""
		return self._sim.visible_scale(sum(actor.workforce.values()), actor.money, actor.prominence())

	def levy_shares(self, scale: float, protection: float = 0.0) -> Any:
		"""(requisition, office) shares of income the state assesses at this visible scale."""
		return self._sim.levy_shares(scale, protection)

	def government(self) -> Any:
		"""The government actor of the founder's civilisation."""
		return self._sim.state_treasury()

	def wage_per_hour(self, trade: str) -> float:
		return self._sim.wage_per_hour(trade)

	@property
	def hours_per_person_year(self) -> float:
		return self._sim.HOURS_PER_PERSON_YEAR

	def hiring_wage_per_hour(self, trade: str) -> float:
		"""What an hour of this trade costs an actor that hires it now: the wage table
		times the premium the local market's recent hiring has built up."""
		return self._sim.wage_per_hour(trade) * self._sim.labour_price_factor(trade)

	def press_labour(self, trade: str, hours: float) -> None:
		"""An actor takes on `hours` a year of a trade: the one local market feels it."""
		self._sim._add_labour_pressure(trade, hours)

	def concern_staff(self, node_id: str) -> Dict[str, float]:
		"""People of each trade running this concern ties up, by the founder's own rule."""
		sim = self._sim
		scholars, craftsmen = sim.venture_hands(node_id)
		foreman_trade, foreman_fte = sim.venture_foreman(node_id)
		staff = {"scholar": scholars, "artisan": craftsmen}
		if foreman_trade:
			staff[foreman_trade] = staff.get(foreman_trade, 0.0) + foreman_fte
		return {trade: people for trade, people in staff.items() if people > 0.0}

	def concern_wage_bill(self, node_id: str) -> float:
		"""Yearly wages of the people running this concern needs, at the going wage."""
		return sum(people * self.hours_per_person_year * self.wage_per_hour(trade)
				   for trade, people in self.concern_staff(node_id).items())

	def free_fte(self, trade: str, actor_id: Optional[str]) -> Optional[float]:
		"""People of a trade left in the pool for this actor after the founder's staff and
		everyone else's. None for a trade nobody here practises yet, which has no pool."""
		sim = self._sim
		if not sim.trade_available(trade) or trade in TRADES_ABSENT:
			return None
		exist = sim.people_who_exist(trade)
		founder = sim.state.household.employees.get(trade, 0.0)
		return max(0.0, exist - founder - sim.actors.staff_fte(trade, excluding=actor_id))

	def copy_cost(self, node_id: str) -> float:
		"""Money the pioneer's version of this work costs, labour included."""
		return self._sim.project_cost(node_id)

	def copy_risk(self, node_id: str) -> float:
		return self._sim.effective_risk(node_id)

	def concern_gross(self, node_id: str) -> float:
		"""Yearly takings of the founder's concern once it has ramped up."""
		sim = self._sim
		return sim.concern_takings(node_id, 1.0) * sim.goods_market_factor(node_id)

	def market_key(self, node_id: str) -> str:
		"""What a concern's operators share: a goods category is one market, any other concern its own."""
		category = self.nodes[node_id].get("cat")
		return category if category in self._sim.GOODS_CATEGORIES else node_id

	def entry_gross(self, node_id: str, rivals: int, entrants: int) -> float:
		"""Yearly takings one more operator would have at full ramp once `entrants` operators
		(itself included) have joined the `rivals` already selling."""
		sim = self._sim
		takings = sim.concern_takings(node_id, 1.0)
		category = self.nodes[node_id].get("cat")
		if category in sim.GOODS_CATEGORIES:
			return takings * sim.goods_category_factor_with_entrants(category, entrants)
		return takings / (rivals + entrants)

	def capital_rate(self) -> float:
		"""Yearly return capital earns lent out at the market's rate."""
		return float(self._sim.civ["starting_interest_rate"])

	def concern_margin(self, node_id: str) -> float:
		"""Yearly profit of the founder's concern once it has ramped up."""
		return self.concern_gross(node_id) - self.upkeep(node_id)

	def proven_concerns(self) -> List[str]:
		"""Founder concerns that have been running at a profit long enough to be believed."""
		sim = self._sim
		projects = sim.state.projects
		proven = []
		for node_id in sorted(projects.operating):
			if node_id in projects.granted or not sim.is_venture(node_id):
				continue
			opened = (projects.opened_year or {}).get(node_id, self.year)
			if self.year - opened >= self.proof_years(node_id) and self.concern_margin(node_id) > 0:
				proven.append(node_id)
		return proven

	def ramp(self, opened_year: int) -> float:
		return min(1.0, (self.year - opened_year + 1) / self._sim.cfg["revenue_ramp_years"])

	def concern_takings(self, node_id: str, opened_year: int, rivals: int = 0) -> float:
		"""Yearly takings of a concern an actor runs. A goods category has one market shared
		by every operator, the founder's and the actors', so each gets its share of the demand;
		a concern with no market model splits with its rivals."""
		sim = self._sim
		takings = sim.concern_takings(node_id, self.ramp(opened_year))
		category = self.nodes[node_id].get("cat")
		if category in sim.GOODS_CATEGORIES:
			return takings * sim.goods_category_factor(category)
		return takings / (1.0 + rivals)

	def concerns_making(self, material: str) -> Any:
		"""The nodes whose concerns put `material` on the market."""
		return supply.nodes_making(material)

	def concern_output_tonnes(self, node_id: str, material: str, opened_year: int, staffed: float) -> float:
		return supply.concern_output_tonnes(self.nodes[node_id], node_id, material,
											self.ramp(opened_year), staffed)

	def upkeep(self, node_id: str) -> float:
		return self.nodes[node_id]["up"] * self._sim.price_index

	def rng_for(self, *parts: Any) -> random.Random:
		"""A random stream keyed by its inputs, so actors never disturb the world's own."""
		digest = hashlib.sha256("|".join(str(part) for part in parts).encode()).hexdigest()
		return random.Random(int(digest[:16], 16))
