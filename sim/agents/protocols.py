"""What an actor may ask of its world: documentation and typing only.

Actors (`Household`, `Firm`, `Government`, `InterestGroup`) never touch the simulation. They are
handed an object that answers the questions below; the engine's own adapter,
`sim/engine/agents_port.py` (`SimWorld`), is the one the running game supplies, and a test or a
second scenario may supply another. Nothing here is imported at run time; it names the members the
actors call, so a change to what an actor asks shows up as a change to this file.
"""
import random
from typing import Any, Dict, List, Optional, Protocol, Set, Tuple

from .revenue import Assessment
from .sector import Sector


class World(Protocol):
	"""The questions an actor asks of the world it lives in."""

	# ---- What a state asks when it budgets

	def edge(self, name: str) -> Any:
		"""The named edge a posting names when its other side is not an actor."""
		...

	def population_total(self) -> float:
		...

	def state_capacity(self) -> float:
		...

	def territory(self) -> Any:
		"""Frontier, coast and road length of the tiles the state holds."""
		...

	def urban_population(self) -> float:
		...

	def subsistence_kg_per_person_year(self) -> float:
		...

	def national_people(self, trade: str) -> float:
		"""People of a trade in the whole country; the working age for unskilled labour."""
		...

	def trade_exists(self, trade: str) -> bool:
		...

	def threat_pressure(self) -> float:
		...

	def army_wanted(self) -> float:
		...

	def soldiers_under_arms(self) -> float:
		"""Soldiers the state keeps now: what it paid for last year, else the force it wants."""
		...

	def patron_ask(self) -> float:
		...

	def equipment_kg_per_soldier(self) -> float:
		...

	def pay_per_person_year(self, trade: str) -> float:
		...

	def commodity_of(self, material: str) -> str:
		...

	def material_cost(self, material: str, tonnes: float) -> float:
		"""Money to buy this many tonnes of a material at the price the market quotes."""
		...

	def local_staff(self, trade: str, people: float) -> float:
		...

	def notice_over(self, scale: float) -> float:
		...

	def visible_taxpayers(self) -> List[Tuple[float, float]]:
		"""(visible scale, taxable income) of every actor the state can see: the founder and the firms."""
		...

	# ---- What a state asks when it assesses revenue

	def revenue_forms(self) -> List[Dict[str, Any]]:
		"""The forms of revenue the civilisation's state raises, as its data declares them."""
		...

	def revenue_assessments(self) -> List[Assessment]:
		...

	def state_revenue(self) -> float:
		"""Money's worth of what the declared forms yield this year, coin and goods taken in kind alike."""
		...

	def harvest_tonnes(self) -> float:
		...

	def material_price(self, material: str) -> float:
		"""Money for one tonne of a material at the price the market quotes."""
		...

	def trade_value(self, direction: str) -> float:
		"""Money's worth of goods imported ("in") or exported ("out") in the last completed year."""
		...

	def coin_stock_value(self) -> float:
		"""Money's worth of the coin this society holds, from its coin standard."""
		...

	def land_rent_paid_by_tile(self) -> Dict[str, float]:
		"""Rent producers paid last year on each tile where land was let, in coin; empty without an agent economy."""
		...

	def land_rent_owners(self) -> List[Tuple[Any, float]]:
		"""(actor, rent received) where the world can say which actors the rent went to; empty where it cannot."""
		...

	# ---- Who is hurt, and what an interest group can see

	def displaced_producers(self) -> List[Sector]:
		...

	def squeezed_employers(self) -> List[Sector]:
		...

	def sectors(self) -> Dict[str, Sector]:
		"""Everyone hurt this year, by key."""
		...

	def group_claims(self) -> Dict[str, float]:
		"""What the state has undertaken to make good to each organised group, by budget line name."""
		...

	def scope_revenue(self, scope: float) -> float:
		"""The state's yearly revenue from a territory holding `scope` of the whole."""
		...

	def founder_protection(self) -> float:
		...

	def lodge_blame(self, amount: float, text: str, year_gap: int, group_record: Any) -> None:
		"""A group's petition puts blame on the founder; the log says who and why, once in a while."""
		...

	def say(self, text: str) -> None:
		"""A line in the founder's log, for a change in who is organised against him."""
		...

	def state_in_deficit(self) -> bool:
		"""Whether the state could pay all it set out to last year."""
		...

	def concession_paid(self, line_name: str) -> float:
		"""What the state paid last year on a named line of its budget."""
		...

	# ---- The loanable-funds market and saving

	def debt_service_share_of_surplus(self) -> float:
		...

	def market_rate(self) -> float:
		...

	def starting_rate(self) -> float:
		...

	def credit_headroom(self, actor_id: str) -> Optional[float]:
		"""What lenders will still advance an actor beyond what others owe; None before the market has met."""
		...

	def state_may_borrow(self, state: Any) -> bool:
		...

	def state_lending(self) -> Tuple[float, float]:
		"""(what the state has out on loan, the yearly rate lenders earn) at the last meeting."""
		...

	def note_interest_paid(self, amount: float) -> None:
		"""A borrower's interest joins the pool lenders are paid from."""
		...

	def household_saving(self) -> float:
		...

	# ---- Disclosure of inventions

	def disclosure_mode(self, node_id: str) -> str:
		...

	def secret_exposure(self, node_id: str) -> float:
		...

	def base_visibility(self, node_id: str) -> float:
		"""How much of an invention can be learned before distance counts, 0..1."""
		...

	def proof_years(self, node_id: str) -> float:
		"""Years a concern must run at a profit before outsiders believe it."""
		...

	def collect_royalty(self, firm: Any, node_id: str, takings: float) -> float:
		"""The founder's royalty on a licensed firm's takings; the amount paid."""
		...

	# ---- Growing a concern

	def span_factor(self, capacity: float) -> float:
		"""Wages of a concern at `capacity` times its founding size, over one founding-size wage bill."""
		...

	def running_cost(self, node_id: str, capacity: float) -> float:
		"""Yearly upkeep and wages of a concern run at `capacity` times its founding size."""
		...

	def expansion_gain(self, node_id: str, opened_year: int, capacity: float, step: float, rivals: float) -> float:
		...

	def plant_cost(self, node_id: str, actor: Any, step: float) -> float:
		"""Money for `step` founding sizes more of a concern's plant, for an actor that already knows how."""
		...

	# ---- The simulated world's own state and the questions a concern asks

	@property
	def year(self) -> int:
		...

	@property
	def nodes(self) -> Dict[str, Any]:
		...

	@property
	def civ_id(self) -> str:
		...

	def baseline_knowledge(self) -> Set[str]:
		"""What the society already knows without the founder."""
		...

	def founder_inventions(self) -> List[str]:
		"""Everything the founder has completed that the society did not have."""
		...

	def demonstrated(self) -> Set[str]:
		...

	def is_public(self, node_id: str) -> bool:
		...

	def exposure(self, node_id: str, location: Optional[str]) -> float:
		"""How much of an invention an observer at `location` can learn, 0..1."""
		...

	def state_weights(self) -> Dict[str, float]:
		...

	def society_output(self) -> float:
		...

	def visible_scale_of(self, actor: Any) -> float:
		"""How large and visible any actor looks to the state: its staff, its wealth and its prominence."""
		...

	def levy_shares(self, scale: float, protection: float = 0.0) -> Any:
		"""(requisition, office) shares of income the state assesses at this visible scale."""
		...

	def government(self) -> Any:
		"""The government actor of the founder's civilisation."""
		...

	@property
	def labour_market(self) -> Any:
		"""The one labour market every employer asks: quote, hire, release, read the pressure."""
		...

	@property
	def hours_per_person_year(self) -> float:
		...

	def concern_staff(self, node_id: str) -> Dict[str, float]:
		"""People of each trade running this concern ties up, by the founder's own rule."""
		...

	def concern_wage_bill(self, node_id: str, capacity: float = 1.0) -> float:
		...

	def site_rent(self, node_id: str, capacity: float = 1.0) -> float:
		"""Yearly rent of the land a concern run at `capacity` times its founding size occupies."""
		...

	def free_fte(self, trade: str, actor_id: Optional[str]) -> Optional[float]:
		...

	def copy_cost(self, node_id: str) -> float:
		"""Money the pioneer's version of this work costs, labour included."""
		...

	def copy_risk(self, node_id: str) -> float:
		...

	def concern_gross(self, node_id: str) -> float:
		"""Yearly takings of the founder's concern once it has ramped up."""
		...

	def market_key(self, node_id: str) -> str:
		"""What a concern's operators share: a goods category is one market, any other concern its own."""
		...

	def entry_gross(self, node_id: str, rivals: float, entrants: float) -> float:
		...

	def concern_margin(self, node_id: str) -> float:
		"""Yearly profit of the founder's concern once it has ramped up."""
		...

	def proven_concerns(self) -> List[str]:
		"""Founder concerns that have been running at a profit long enough to be believed."""
		...

	def ramp(self, opened_year: int, node_id: Optional[str] = None) -> float:
		...

	def scale_ceiling(self, node_id: str) -> float:
		"""The most founding sizes one concern of this kind can be run at."""
		...

	def concern_takings(self, node_id: str, opened_year: int, rivals: float = 0.0, capacity: float = 1.0) -> float:
		...

	def concerns_making(self, material: str) -> Any:
		"""The nodes whose concerns put `material` on the market."""
		...

	def materials_made_by(self, node_id: str) -> Any:
		"""The materials a concern puts on the market."""
		...

	def market_forget(self, actor_id: str) -> None:
		"""An actor's standing sales and purchases in the one goods market end; it deals afresh this year."""
		...

	def runs_agent_economy(self) -> bool:
		...

	def market_sale(self, seller_id: str, material: str, tonnes: float, from_concerns: Any = None) -> None:
		...

	def market_purchase(self, buyer_id: str, commodity: str, tonnes: float) -> None:
		"""An actor buys `tonnes` of a commodity at the one goods market this year."""
		...

	def concern_output_tonnes(self, node_id: str, material: str, opened_year: int, staffed: float) -> float:
		...

	def upkeep(self, node_id: str, capacity: float = 1.0) -> float:
		...

	def rng_for(self, *parts: Any) -> random.Random:
		"""A random stream keyed by its inputs, so actors never disturb the world's own."""
		...

	# ---- What a trader asks (sim/engine/agents_port_trade.py)

	def trade_places(self, location: Optional[str]) -> List[str]:
		"""Places with a market a trader at `location` can reach; None for every place."""
		...

	def trade_materials(self) -> List[str]:
		"""Materials that may be carried between places."""
		...

	def price_at(self, material: str, place: str) -> Optional[float]:
		"""Money per tonne of a material at a place, in home money; None where it has no price."""
		...

	def price_after_cargo(self, material: str, place: str, tonnes: float, landing: bool) -> Optional[float]:
		"""Money per tonne at a place once `tonnes` more land there (`landing`) or are taken from it, on top of
		the year's cargo; None where the place's market does not answer."""
		...

	def freight_between(self, source: str, destination: str, material: str, tonnes: float) -> float:
		"""Money to carry `tonnes` of a material from one place to another."""
		...

	def market_depth(self, material: str, place: str) -> float:
		"""Tonnes a year buyers at a place take of a material."""
		...

	def delivered_this_year(self, material: str, destination: str) -> float:
		"""Tonnes every shipper has brought to a place so far this year, from any source."""
		...

	def ship(self, trader_id: str, material: str, tonnes: float, source: str, destination: str) -> Tuple[float, float]:
		"""Buy at the source and sell at the destination: (money paid, money received)."""
		...

	def country_of_place(self, place: str) -> Optional[str]:
		"""The country a place belongs to; None for the home country."""
		...

	# ---- What a country, a body of people and the cast ask (sim/engine/agents_port_cast.py)

	def distance_km(self, place_a: Optional[str], place_b: Optional[str]) -> float:
		"""Kilometres between two places (tile or region ids); None is where the founder operates from."""
		...

	def subsistence_cost_per_person_year(self) -> float:
		"""Money for one person's food at subsistence for a year."""
		...

	def need_floor_costs_per_person_year(self) -> Dict[str, float]:
		"""Money for one person's floor of each need for a year, by need id, at the prices households pay
		(the need-basket kernel, sim/world/need_basket.py)."""
		...

	def observed_stratum(self, country: Optional[str], name: str) -> Optional[Dict[str, float]]:
		"""Headcount and income ("members", "income") another model already keeps for a body of people."""
		...

	# ---- What a state asks about its coin (sim/engine/agents_port_coinage.py)

	def coin_regime(self) -> str:
		"""The civilisation's coin standard regime: "struck_coin", "weighed_metal", "commodity" or "fiat"."""
		...

	# ---- What patents ask (sim/engine/agents_port_disclosure.py)

	def state_grants_patents(self, actor: Any) -> bool:
		"""Whether the state over an actor knows a technique declaring the patent mechanic."""
		...

	def patent_entry(self, node_id: str) -> Optional[Dict[str, Any]]:
		"""The live patent on a node ({"holder", "expires", "licensees"}), else None."""
		...

	# ---- What the home state asks of its people (sim/engine/agents_port_budget.py)

	def country_strata(self) -> List[Any]:
		"""The home country's bodies of people, in id order."""
		...
