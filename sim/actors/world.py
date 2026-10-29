"""What an actor can see and price: a read-only view of the simulated world.

Actors never touch the game directly. They ask this view, which answers from the views the actors module reads, which
keeps them free of the engine and lets a test or a second scenario supply another one.
"""
import hashlib
import math
import random
from typing import Any, Dict, List, Optional, Set, Tuple

from sim.agents.api import OBSERVATION_RANGE_KM, business_books, business_plant_books, SECRET_EXPOSURE, demand_answer, payroll, supply
from sim.unit_conversions import KILOGRAMS_PER_TONNE

from sim.reporting.api import output_rules
from sim.markets.api import ForgetActorOrders, NoteActorPurchase, NoteActorSale
from sim.seats import api as seats_api
from sim.world import plant_figures
from sim.world.material_units import tonnes_per_unit  # noqa: F401  (the trade view reads it from here)

from .world_budget import BudgetView
from .world_capacity import CapacityView
from .world_capital import CapitalView
from .world_cast import CastView
from .world_coinage import CoinageView
from .world_disclosure import DisclosureView
from .world_enterprises import EnterpriseView
from .world_groups import GroupView
from .world_patronage import PatronageView
from .world_research import ResearchView
from .world_review import ReviewView
from .world_revenue import RevenueView
from .world_seats import SeatView
from .world_site import SiteView
from .world_stakes import StakeView
from .world_trade import TradeView


class ActorWorld(BudgetView, SiteView, RevenueView, GroupView, PatronageView, StakeView, DisclosureView, CapitalView, CapacityView,
                 TradeView, CastView, CoinageView, SeatView, ReviewView, EnterpriseView, ResearchView):
	"""The answers to the questions actors ask, read through the views of the module that hands this world out."""

	def __init__(self, module: Any) -> None:
		self.module = module
		self.needs = module.needs
		# Answers that hold for the whole of one yearly turn.
		self._memo: Dict[str, Any] = {}

	@property
	def goods_category_names(self) -> Any:
		"""The goods categories: concerns in them share one market."""
		return self.needs.goods_categories()

	@property
	def registry(self) -> Any:
		"""The cast of actors the module keeps."""
		return self.module.cast()

	def _shared(self, ask: Any, *arguments: Any) -> Any:
		"""`ask(*arguments)` with this view's table of shared answers open."""
		with self.needs.shared_answers(self._memo.setdefault("shared", {})):
			return ask(*arguments)

	def _once(self, key: str, compute: Any) -> Any:
		if key not in self._memo:
			self._memo[key] = compute()
		return self._memo[key]

	def edge(self, name: str) -> Any:
		"""The named edge a posting names when its other side is not an actor."""
		return self.module.edge(name)

	def pay_wages(self, payer: Any, amount: float, purpose: Any) -> None:
		"""Wages the home country's people are paid: they reach the strata's purses."""
		payroll.pay_wages(self.registry, payer, amount, purpose, self)

	@property
	def year(self) -> int:
		return self.needs.year()

	@property
	def nodes(self) -> Dict[str, Any]:
		return self.needs.tree_nodes()

	@property
	def civ_id(self) -> str:
		return str(self.needs.civilisation().get("id"))

	def baseline_knowledge(self) -> Set[str]:
		"""What the society already knows without the founder."""
		return self._once("baseline", lambda: set(self.needs.techniques_granted()))

	def founder_inventions(self) -> List[str]:
		"""Everything any seat has completed that the society did not have."""
		return self._once("inventions", lambda: sorted(seats_api.built_by_any(self.needs.techniques_by_seat())))

	def _registry_actors(self) -> List[Any]:
		return list(self.registry.actors.values())

	def actor_held(self) -> Dict[str, List[Any]]:
		"""Every node an active actor holds beyond what the society already knew, with its holders in id order."""
		def compute() -> Dict[str, List[Any]]:
			baseline = self.baseline_knowledge()
			held: Dict[str, List[Any]] = {}
			for actor in sorted(self._registry_actors(), key=lambda actor: actor.identity()):
				if actor.record.exited_year is not None:
					continue
				for node_id in sorted(actor.knowledge):
					if node_id in self.nodes and node_id not in baseline:
						held.setdefault(node_id, []).append(actor)
			return held
		return self._once("actor_held", compute)

	def demonstrated(self) -> Set[str]:
		"""What can be seen made: every seat's builds and every actor's own knowledge."""
		return self._once("demonstrated", lambda: set(self.founder_inventions()) | set(self.actor_held()))

	def knowledge_half_life_years(self) -> float:
		return self.needs.knowledge_half_life_years()

	def knowledge_visibility(self, node_id: str, distance_km: float) -> float:
		"""How much of a node some actor holds shows `distance_km` away: its own opacity, public if a seat runs it."""
		visibility = seats_api.base_visibility("default", self.is_public(node_id), self.needs.copy_difficulty[node_id], SECRET_EXPOSURE)
		return seats_api.seen_from(visibility, distance_km, OBSERVATION_RANGE_KM)

	def is_public(self, node_id: str) -> bool:
		"""Whether some seat runs it as a concern, where anyone can see it."""
		return seats_api.operating_anywhere(self.needs.legacy_seats(), node_id)

	def exposure(self, node_id: str, location: Optional[str]) -> float:
		"""How much of an invention an observer at `location` can learn, 0..1: the best view of any seat
		that built it, from that seat's own place (the acting seat's when no seat built it)."""
		needs = self.needs
		builders = seats_api.builders_of(needs.techniques_by_seat(), node_id)
		holders = self.actor_held().get(node_id, [])
		if not builders and not holders:
			builders = [needs.acting_seat()]
		public = self.is_public(node_id)
		best = 0.0
		for seat_id in builders:
			mode = (needs.disclosures[seat_id].get(node_id) or {}).get("mode", "default")
			visibility = seats_api.base_visibility(mode, public, needs.copy_difficulty[node_id], SECRET_EXPOSURE)
			if location is not None:
				visibility = seats_api.seen_from(
					visibility, self.distance_km(location, needs.seat_place[seat_id]), OBSERVATION_RANGE_KM)
			best = max(best, visibility)
		for holder in holders:
			best = max(best, self.knowledge_visibility(
				node_id, self.distance_km(holder.location(), location) if location is not None else 0.0))
		return best

	def state_weights(self) -> Dict[str, float]:
		return self._once("weights", self.needs.state_trait_weights)

	def society_output(self) -> float:
		"""Yearly value of what the society's market sells: quantities this year at the opening's prices
		(sim/reporting/output.py), in this civilisation's money."""
		def compute() -> float:
			producing = output_rules.share_producing(self.needs.working_age(), self.soldiers_under_arms())
			return self.needs.economy_output_value() * producing
		return self._once("output", compute)

	def visible_scale_of(self, actor: Any) -> float:
		"""How large and visible any actor looks to the state: its staff, its wealth and its prominence."""
		return self.needs.visible_scale(sum(actor.workforce.values()), demand_answer.visible_wealth(actor.money, actor.concealed_wealth()),
										actor.prominence(), actor.defiance())

	def levy_shares(self, scale: float, protection: float = 0.0, state: Any = None) -> Any:
		"""(requisition, office) shares of income the state assesses at this visible scale."""
		return self.needs.levy_shares(scale, protection, state)

	def government(self) -> Any:
		"""The government actor of the founder's civilisation."""
		return self.module.state_treasury()

	@property
	def labour_market(self) -> Any:
		"""The one labour market every employer asks: quote, hire, release, read the pressure."""
		return self.needs.labour_market()

	@property
	def hours_per_person_year(self) -> float:
		return self.needs.hours_per_person_year()

	def concern_staff(self, node_id: str) -> Dict[str, float]:
		"""People of each trade one plant of this concern needs: the one crew rule (business_crew_rule), which reads the plant's data."""
		return self.needs.concern_staff[node_id]

	def concern_wage_bill(self, node_id: str, capacity: float = 1.0) -> float:
		"""Yearly wages of the people running this concern needs, at the going wage, for a firm
		running it at `capacity` times its founding size."""
		return self.span_factor(capacity) * sum(
			people * self.hours_per_person_year * self.labour_market.quote(trade)
			for trade, people in self.concern_staff(node_id).items())

	def hourly_pay(self, trade: str) -> Optional[float]:
		"""What an hour of a trade pays at the going wage of the home labour market."""
		return float(self.labour_market.quote(trade, 0.0))

	def plant_costs(self, node_id: str) -> Optional[Tuple[float, float]]:
		"""(upkeep, wage bill) of a plant of the concern at its founding size at home."""
		return business_plant_books.home_costs(self, node_id)

	def free_fte(self, trade: str, actor_id: Optional[str]) -> Optional[float]:
		"""People of a trade left in the pool for this actor after the founder's staff and
		everyone else's. A trade nobody here practises has the people the founder taught as its pool;
		None for a trade that cannot be had at all."""
		needs = self.needs
		if not needs.trade_available[trade]:
			return None
		exist = needs.taught_trade_people[trade] if trade in needs.trades_absent() else needs.people_who_exist[trade]
		founder = needs.staff_on_all_books[trade]
		return max(0.0, exist - founder - self.registry.home_staff_fte(trade, excluding=actor_id))

	def copy_cost(self, node_id: str) -> float:
		"""Money the pioneer's version of this work costs, labour included."""
		return self._shared(self.needs.project_cost, node_id)

	def copy_risk(self, node_id: str) -> float:
		return self.needs.effective_risk(node_id)

	def concern_gross(self, node_id: str) -> float:
		"""Yearly takings of the founder's concern once it has ramped up."""
		return self.needs.concern_gross(node_id)

	def market_key(self, node_id: str) -> str:
		"""What a concern's operators share: a goods category is one market, any other concern its own."""
		category = self.nodes[node_id].get("cat")
		return category if category in self.goods_category_names else node_id

	def entry_gross(self, node_id: str, rivals: float, entrants: float) -> float:
		"""Yearly takings one more operator would have at full ramp once `entrants` operators
		(itself included) have joined the `rivals` already selling."""
		needs = self.needs
		takings = needs.concern_takings(node_id, 1.0) * needs.node_output_market_factor(self.nodes[node_id])
		category = self.nodes[node_id].get("cat")
		if category in self.goods_category_names:
			return takings * needs.goods_category_factor_with_entrants(category, entrants)
		return takings / (rivals + entrants)

	def concern_margin(self, node_id: str) -> float:
		"""Yearly profit of the founder's concern once it has ramped up."""
		return self.concern_gross(node_id) - self.upkeep(node_id)

	def proven_concerns(self) -> List[str]:
		"""Concerns any seat has run at a profit long enough to be believed."""
		needs = self.needs
		proven: Set[str] = set()
		for seat_id in needs.seat_list()["playing"] or [needs.acting_seat()]:
			with needs.acting_as(seat_id):
				proven.update(self._proven_concerns_of_acting_seat())
		return sorted(proven)

	def _proven_concerns_of_acting_seat(self) -> List[str]:
		needs = self.needs
		projects = needs.legacy_projects()
		granted = needs.techniques_granted()
		proven = []
		for node_id in sorted(projects.operating):
			if node_id in granted or not needs.is_venture[node_id]:
				continue
			opened = projects.business.opened_year_of(node_id, self.year)
			if self.year - opened >= self.proof_years(node_id) and self.concern_margin(node_id) > 0:
				proven.append(node_id)
		return proven

	def ramp(self, opened_year: int, node_id: Optional[str] = None) -> float:
		depth = 0.0 if node_id is None else self.needs.industry_depth[node_id]
		return plant_figures.ramp(self.year - opened_year, self.needs.game_setting["revenue_ramp_years"], depth,
								  self.needs.ramp_share_at_full_depth())

	def scale_ceiling(self, node_id: str) -> float:
		"""The most founding sizes one concern of this kind can be run at, from the industry's experience."""
		return float(self.needs.industry_scale_ceiling[node_id])

	def concern_takings(self, node_id: str, opened_year: int, rivals: float = 0.0, capacity: float = 1.0) -> float:
		"""Yearly takings of a concern an actor runs at `capacity` times its founding size. A goods
		category has one market shared by every operator, the founder's and the actors', so each unit
		of capacity gets its share of the demand; a concern with no market model splits with the
		capacity of its rivals."""
		needs = self.needs
		takings = business_books.takings_of_size(needs.concern_takings(node_id, self.ramp(opened_year, node_id)), capacity,
												 needs.node_output_market_factor(self.nodes[node_id]))
		category = self.nodes[node_id].get("cat")
		if category in self.goods_category_names:
			return takings * needs.goods_category_factor(category)
		return takings / (capacity + rivals)

	def concerns_making(self, material: str) -> Any:
		"""The nodes whose concerns put `material` on the market."""
		return supply.nodes_making(material)

	def materials_made_by(self, node_id: str) -> Any:
		"""The materials a concern puts on the market."""
		return supply.materials_made_by(node_id)

	def market_forget(self, actor_id: str) -> None:
		"""An actor's sales and purchases noted for this year's market end; it deals afresh."""
		self.needs.send(ForgetActorOrders(actor_id))

	def market_sale(self, seller_id: str, material: str, tonnes: float, from_concerns: Any = None) -> None:
		"""An actor sells `tonnes` of a material into the one goods market this year. One whose concerns
		made it, [(node id, tonnes)], will not sell below what they cost it to make. The goods are offered in the agent
		economy's book and the proceeds reach the seller's purse when the year's market has cleared."""
		self.needs.send(NoteActorSale(seller_id, material, tonnes, from_concerns))

	def market_purchase(self, buyer_id: str, commodity: str, tonnes: float, budget: float = 0.0) -> None:
		"""An actor buys `tonnes` of a commodity at the one goods market this year: it bids for them in the agent
		economy's book, paying up to `budget` out of its purse."""
		self.needs.send(NoteActorPurchase(buyer_id, commodity, tonnes, budget))

	def sells_on_book(self, node_id: str) -> bool:
		"""Whether what a concern makes is sold in the agent economy's book, so its takings are the market's and not the
		engine's estimate."""
		return any(self.needs.agent_trades_good[material] for material in supply.materials_made_by(node_id))

	def concern_output_tonnes(self, node_id: str, material: str, opened_year: int, staffed: float) -> float:
		node = self.nodes[node_id]
		if not node.get("annual_output_t"):
			return supply.concern_output_tonnes(node, node_id, material, self.ramp(opened_year, node_id), staffed,
												self._derived_tonnes(node_id, material))
		return supply.concern_output_tonnes(node, node_id, material,
											self.ramp(opened_year, node_id), staffed
											* self.needs.concern_volume_ratio(node_id))

	def _derived_tonnes(self, node_id: str, material: str) -> float:
		"""Tonnes a year of a material the concern's staff and plant turn out now, from the production data (its
		baskets), the mass of a unit of the material taken from what the data states of it."""
		baskets = self.needs.concern_baskets_now[node_id]
		units = 0.0 if baskets is None else baskets.outputs.get(material, 0.0)
		if units <= 0.0:
			return 0.0
		kilograms = self.needs.unit_mass_kg(material)
		return units * kilograms / KILOGRAMS_PER_TONNE if math.isfinite(kilograms) else 0.0

	def upkeep(self, node_id: str, capacity: float = 1.0) -> float:
		return self.needs.concern_upkeep(node_id, capacity)

	def rng_for(self, *parts: Any) -> random.Random:
		"""A random stream keyed by its inputs, so actors never disturb the world's own."""
		digest = hashlib.sha256("|".join(str(part) for part in parts).encode()).hexdigest()
		return random.Random(int(digest[:16], 16))
