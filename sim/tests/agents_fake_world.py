"""A small stand-in world for unit tests of `sim/agents/` mechanisms: no `Sim`, no data files.

It answers the questions in `sim/agents/protocols.py` that the common actor mechanisms ask
(imitation, borrowing, staffing and running a concern, selling, the labour market) from plain
dictionaries a test fills in. A test that needs a member this does not have subclasses it in its
own file, so tests owning different mechanisms never edit this one together.
"""
import random
from typing import Any, Dict, List, Optional, Set


class FakeLabourMarket:
	"""Every trade is paid one flat wage per hour; hiring and release are only counted."""

	def __init__(self, wage_per_hour: float = 1.0) -> None:
		self.wage_per_hour = wage_per_hour
		self.hired: Dict[str, float] = {}

	def quote(self, trade: str, hours: float, actor: Any = None) -> float:
		return self.wage_per_hour

	def hire(self, actor: Any, trade: str, hours: float) -> None:
		self.hired[trade] = self.hired.get(trade, 0.0) + hours

	def release(self, actor: Any, trade: str, hours: float) -> None:
		self.hired[trade] = self.hired.get(trade, 0.0) - hours


class FakeGovernment:
	"""Takes nothing; records what it was asked to collect."""

	def __init__(self) -> None:
		self.asked: List[float] = []

	def collect(self, actor: Any, takings: float, world: Any) -> float:
		self.asked.append(takings)
		return 0.0


def make_node(node_id: str, prerequisites=(), hours: float = 100.0, years: float = 1.0,
			  revenue: float = 0.0, upkeep: float = 0.0, makes=()) -> Dict[str, Any]:
	"""A tree node with the fields the actor mechanisms read."""
	return {"id": node_id, "name": node_id, "pre": list(prerequisites), "lab": {"labourer": hours},
			"yrs": years, "rev": revenue, "up": upkeep, "risk": 0.0, "makes": list(makes)}


class FakeWorld:
	"""The world one country's actors see. Fill `nodes`, `baseline`, `demonstrated_nodes`, `prices`."""

	hours_per_person_year = 2000.0

	def __init__(self, year: int = 100, seed: int = 1) -> None:
		self.year = year
		self.seed = seed
		self.civ = "home"
		self.nodes: Dict[str, Dict[str, Any]] = {}
		self.baseline: Set[str] = set()
		self.demonstrated_nodes: Set[str] = set()
		self.public_nodes: Set[str] = set()
		self.labour_market = FakeLabourMarket()
		self.government_actor: Any = FakeGovernment()
		self.rate = 0.05
		# trade -> people free to hire (None = unlimited)
		self.free_people: Dict[str, Optional[float]] = {}
		# material -> price per tonne
		self.prices: Dict[str, float] = {}
		self.sales: List[Any] = []
		self.purchases: List[Any] = []
		self.interest_paid = 0.0
		self.output = 1_000_000.0
		# concerns that have run at a profit where entrants can see them
		self.proven: Set[str] = set()

	# ---- the tree and what has been shown
	def civ_id(self) -> str:
		return self.civ

	def baseline_knowledge(self) -> Set[str]:
		return self.baseline

	def demonstrated(self) -> Set[str]:
		return self.demonstrated_nodes

	def founder_inventions(self) -> List[str]:
		return sorted(self.demonstrated_nodes - self.baseline)

	def is_public(self, node_id: str) -> bool:
		return node_id in self.public_nodes

	def exposure(self, node_id: str, location: Optional[str]) -> float:
		return 1.0

	def copy_cost(self, node_id: str) -> float:
		return float(self.nodes[node_id].get("cost", 100.0))

	def copy_risk(self, node_id: str) -> float:
		return float(self.nodes[node_id].get("risk", 0.0))

	def rng_for(self, *parts: Any) -> random.Random:
		return random.Random(repr((self.seed,) + parts))

	# ---- money and credit
	def market_rate(self) -> float:
		return self.rate

	def starting_rate(self) -> float:
		return self.rate

	def debt_service_share_of_surplus(self) -> float:
		return 0.5

	def credit_headroom(self, actor_id: str) -> Optional[float]:
		return None

	def note_interest_paid(self, amount: float) -> None:
		self.interest_paid += amount

	def collect_royalty(self, actor: Any, node_id: str, takings: float) -> float:
		return 0.0

	def government(self) -> Any:
		return self.government_actor

	# ---- staffing and running a concern
	def concern_staff(self, node_id: str) -> Dict[str, float]:
		return {trade: hours / self.hours_per_person_year
				for trade, hours in (self.nodes[node_id].get("lab") or {}).items()}

	def free_fte(self, trade: str, actor_id: Optional[str]) -> Optional[float]:
		return self.free_people.get(trade)

	def concern_wage_bill(self, node_id: str, capacity: float = 1.0) -> float:
		return capacity * sum(people * self.hours_per_person_year * self.labour_market.wage_per_hour
							  for people in self.concern_staff(node_id).values())

	def concern_takings(self, node_id: str, opened_year: int, rivals: float = 0.0, capacity: float = 1.0) -> float:
		return capacity * float(self.nodes[node_id].get("rev", 0.0)) / (1.0 + rivals)

	def upkeep(self, node_id: str, capacity: float = 1.0) -> float:
		return capacity * float(self.nodes[node_id].get("up", 0.0))

	def materials_made_by(self, node_id: str) -> List[str]:
		return list(self.nodes[node_id].get("makes") or ())

	def concerns_making(self, material: str) -> Set[str]:
		return {node_id for node_id, node in self.nodes.items() if material in (node.get("makes") or ())}

	def concern_output_tonnes(self, node_id: str, material: str, opened_year: int, staffed: float) -> float:
		return staffed

	# ---- what the built-in spawners ask (firm entry, interest groups)
	def society_output(self) -> float:
		return self.output

	def proven_concerns(self) -> List[str]:
		return sorted(self.proven)

	def market_key(self, node_id: str) -> str:
		return node_id

	def sectors(self) -> Dict[str, Any]:
		return {}

	# ---- what traders ask: no places to trade between unless a test subclass names some
	def trade_places(self, location: Optional[str]) -> List[str]:
		return []

	def trade_materials(self) -> List[str]:
		return []

	# ---- the goods market
	def market_forget(self, actor_id: str) -> None:
		pass

	def runs_agent_economy(self) -> bool:
		return False

	def market_sale(self, seller_id: str, material: str, tonnes: float, from_concerns: Any = None) -> None:
		self.sales.append((seller_id, material, tonnes))

	def market_purchase(self, buyer_id: str, commodity: str, tonnes: float) -> None:
		self.purchases.append((buyer_id, commodity, tonnes))

	def material_price(self, material: str) -> float:
		return self.prices.get(material, 0.0)

	def material_cost(self, material: str, tonnes: float) -> float:
		return self.material_price(material) * tonnes


def total_money(actors) -> float:
	"""Money held by these actors together: what a conservation check compares before and after."""
	return sum(actor.money for actor in actors)
