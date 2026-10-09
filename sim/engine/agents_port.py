"""What an actor can see and price: a read-only view of the simulated world.

Actors never touch `Sim` directly. They ask this view, which keeps them free
of the engine and lets a test or a second scenario supply another one.
"""
import hashlib
import random
from typing import Any, Dict, List, Optional, Set

from sim.agents.api import OBSERVATION_RANGE_KM, payroll, supply

from .agents_port_budget import BudgetView
from .agents_port_capacity import CapacityView
from .agents_port_capital import CapitalView
from .agents_port_disclosure import DisclosureView
from .agents_port_groups import GroupView
from .agents_port_revenue import RevenueView
from .agents_port_cast import CastView
from .agents_port_coinage import CoinageView
from .agents_port_trade import TradeView
from .data import TRADES_ABSENT
from .industry_depth import RAMP_SHARE_AT_FULL_DEPTH


class SimWorld(BudgetView, RevenueView, GroupView, DisclosureView, CapitalView, CapacityView, TradeView, CastView, CoinageView):
	"""The `Sim`'s answers to the questions actors ask."""

	def __init__(self, sim: Any) -> None:
		self._sim = sim
		# Answers that hold for the whole of one yearly turn.
		self._memo: Dict[str, Any] = {}

	def _shared(self, ask: Any, *arguments: Any) -> Any:
		"""`ask(*arguments)` with this view's table of shared answers open (see engine/view_share.py)."""
		sim = self._sim
		opened = sim.open_view_scope(self._memo.setdefault("shared", {}))
		try:
			return ask(*arguments)
		finally:
			sim.close_view_scope(opened)

	def _once(self, key: str, compute: Any) -> Any:
		if key not in self._memo:
			self._memo[key] = compute()
		return self._memo[key]

	def edge(self, name: str) -> Any:
		"""The named edge a posting names when its other side is not an actor."""
		return self._sim.edge(name)

	def pay_wages(self, payer: Any, amount: float, purpose: Any) -> None:
		"""Wages the home country's people are paid: they reach the strata's purses."""
		payroll.pay_wages(self._sim.actors, payer, amount, purpose, self)

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
		distance = self.distance_km(location, None)  # type: ignore[attr-defined]
		return visibility / (1.0 + distance / OBSERVATION_RANGE_KM)

	def state_weights(self) -> Dict[str, float]:
		return self._once("weights", self._sim.state_trait_weights)

	def society_output(self) -> float:
		"""Yearly value of what the society's market sells: quantities this year at the opening's prices
		(real_output.py), in this civilisation's money."""
		sim = self._sim
		def compute() -> float:
			# TEMPORARY HEURISTIC (CLAUDE.md 4.4): the market's quantities do not yet fall when
			# people are drawn off to arms, so the share of working people not under arms scales them
			working = sim.population.working_age
			producing = max(0.0, working - self.soldiers_under_arms()) / working if working > 0.0 else 1.0
			return sim.economy.output_value() * producing
		return self._once("output", compute)

	def visible_scale_of(self, actor: Any) -> float:
		"""How large and visible any actor looks to the state: its staff, its wealth and its prominence."""
		return self._sim.visible_scale(sum(actor.workforce.values()), actor.money, actor.prominence())

	def levy_shares(self, scale: float, protection: float = 0.0) -> Any:
		"""(requisition, office) shares of income the state assesses at this visible scale."""
		return self._sim.levy_shares(scale, protection)

	def government(self) -> Any:
		"""The government actor of the founder's civilisation."""
		return self._sim.state_treasury()

	@property
	def labour_market(self) -> Any:
		"""The one labour market every employer asks: quote, hire, release, read the pressure."""
		return self._sim.economy.labour

	@property
	def hours_per_person_year(self) -> float:
		return self._sim.HOURS_PER_PERSON_YEAR

	def concern_staff(self, node_id: str) -> Dict[str, float]:
		"""People of each trade running this concern ties up, by the founder's own rule."""
		sim = self._sim
		scholars, craftsmen = sim.venture_hands(node_id)
		foreman_trade, foreman_fte = sim.venture_foreman(node_id)
		staff = {"scholar": scholars, "artisan": craftsmen}
		if foreman_trade:
			staff[foreman_trade] = staff.get(foreman_trade, 0.0) + foreman_fte
		return {trade: people for trade, people in staff.items() if people > 0.0}

	def concern_wage_bill(self, node_id: str, capacity: float = 1.0) -> float:
		"""Yearly wages of the people running this concern needs, at the going wage, for a firm
		running it at `capacity` times its founding size."""
		return self.span_factor(capacity) * sum(
			people * self.hours_per_person_year * self.labour_market.quote(trade)
			for trade, people in self.concern_staff(node_id).items())

	def free_fte(self, trade: str, actor_id: Optional[str]) -> Optional[float]:
		"""People of a trade left in the pool for this actor after the founder's staff and
		everyone else's. None for a trade nobody here practises yet, which has no pool."""
		sim = self._sim
		if not sim.labour.trade_available(trade) or trade in TRADES_ABSENT:
			return None
		exist = sim.labour.people_who_exist(trade)
		founder = sim.state.household.employees.get(trade, 0.0)
		return max(0.0, exist - founder - sim.actors.staff_fte(trade, excluding=actor_id))

	def copy_cost(self, node_id: str) -> float:
		"""Money the pioneer's version of this work costs, labour included."""
		return self._shared(self._sim.economy.project_cost, node_id)

	def copy_risk(self, node_id: str) -> float:
		return self._sim.effective_risk(node_id)

	def concern_gross(self, node_id: str) -> float:
		"""Yearly takings of the founder's concern once it has ramped up."""
		return self._sim.economy.concern_gross(node_id)

	def market_key(self, node_id: str) -> str:
		"""What a concern's operators share: a goods category is one market, any other concern its own."""
		category = self.nodes[node_id].get("cat")
		return category if category in self._sim.GOODS_CATEGORIES else node_id

	def entry_gross(self, node_id: str, rivals: float, entrants: float) -> float:
		"""Yearly takings one more operator would have at full ramp once `entrants` operators
		(itself included) have joined the `rivals` already selling."""
		sim = self._sim
		takings = sim.concern_takings(node_id, 1.0) * sim.node_output_market_factor(self.nodes[node_id])
		category = self.nodes[node_id].get("cat")
		if category in sim.GOODS_CATEGORIES:
			return takings * sim.goods_category_factor_with_entrants(category, entrants)
		return takings / (rivals + entrants)

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

	def ramp(self, opened_year: int, node_id: Optional[str] = None) -> float:
		ramp_years = self._sim.cfg["revenue_ramp_years"]
		if node_id is not None:
			ramp_years *= 1.0 - (1.0 - RAMP_SHARE_AT_FULL_DEPTH) * self._sim.industry_depth(node_id)
		return min(1.0, (self.year - opened_year + 1) / ramp_years)

	def scale_ceiling(self, node_id: str) -> float:
		"""The most founding sizes one concern of this kind can be run at, from the industry's experience."""
		return float(self._sim.industry_scale_ceiling(node_id))

	def concern_takings(self, node_id: str, opened_year: int, rivals: float = 0.0, capacity: float = 1.0) -> float:
		"""Yearly takings of a concern an actor runs at `capacity` times its founding size. A goods
		category has one market shared by every operator, the founder's and the actors', so each unit
		of capacity gets its share of the demand; a concern with no market model splits with the
		capacity of its rivals."""
		sim = self._sim
		takings = (sim.concern_takings(node_id, self.ramp(opened_year, node_id)) * capacity
				   * sim.node_output_market_factor(self.nodes[node_id]))
		category = self.nodes[node_id].get("cat")
		if category in sim.GOODS_CATEGORIES:
			return takings * sim.goods_category_factor(category)
		return takings / (capacity + rivals)

	def concerns_making(self, material: str) -> Any:
		"""The nodes whose concerns put `material` on the market."""
		return supply.nodes_making(material)

	def materials_made_by(self, node_id: str) -> Any:
		"""The materials a concern puts on the market."""
		return supply.materials_made_by(node_id)

	def market_forget(self, actor_id: str) -> None:
		"""An actor's standing sales and purchases in the one goods market end; it deals afresh this year."""
		self._sim.economy.goods.forget(actor_id)

	def runs_agent_economy(self) -> bool:
		return self._sim.economy.runs_agent_economy()

	def market_sale(self, seller_id: str, material: str, tonnes: float, from_concerns: Any = None) -> None:
		"""An actor sells `tonnes` of a material into the one goods market this year. One whose concerns
		made it, [(node id, tonnes)], will not sell below what they cost it to make."""
		self._sim.economy.offer_sale(seller_id, material, tonnes, from_concerns)

	def market_purchase(self, buyer_id: str, commodity: str, tonnes: float) -> None:
		"""An actor buys `tonnes` of a commodity at the one goods market this year."""
		self._sim.economy.goods.note_purchase(buyer_id, commodity, tonnes)

	def concern_output_tonnes(self, node_id: str, material: str, opened_year: int, staffed: float) -> float:
		return supply.concern_output_tonnes(self.nodes[node_id], node_id, material,
											self.ramp(opened_year, node_id), staffed
											* self._sim.concern_volume_ratio(node_id))

	def upkeep(self, node_id: str, capacity: float = 1.0) -> float:
		return self._sim.economy.concern_upkeep(node_id, capacity)

	def rng_for(self, *parts: Any) -> random.Random:
		"""A random stream keyed by its inputs, so actors never disturb the world's own."""
		digest = hashlib.sha256("|".join(str(part) for part in parts).encode()).hexdigest()
		return random.Random(int(digest[:16], 16))
