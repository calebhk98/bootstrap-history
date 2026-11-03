"""`Actor`: anything that owns money, staff, know-how and works, and decides.

The shared surface is `money`, `workforce`, `knowledge`, `concerns` and
`works`. Subclasses say where that state lives (the founder's household
delegates to the simulation state; a `RecordedActor` keeps an `ActorRecord`)
and what they value. Decisions go through the actor's `decision_policy`.
"""
from typing import Any, Dict, List, Optional, Set

from .business import Business, PlantKeys
from .records import ActorRecord

from . import imitation, research_choice
from .actor_copying import ActorCopying
from .actor_holdings import ActorHoldings, RecordedHoldings
from .actor_output import ActorOutput
from .actor_payments import ActorPayments, RecordedPayments
from .actor_review import ActorReview
from .actor_stance import ActorStance, RecordedStance
from .borrowing import Borrower
from .purses import Purses
from .policy import Policy, ValuePolicy


class Actor(Borrower):
	kind = "actor"
	keeps_purchases = False   # whether what the actor buys at the market joins its stores
	researches = False   # whether the actor does research and takes part in knowledge spreading (`research.py`)
	purses: Any = None   # the book of purses the actor keeps its account in, when it keeps one

	def __init__(self, policy: Optional[Policy] = None) -> None:
		self.decision_policy = policy or ValuePolicy()
		self.stance: ActorStance = ActorStance(self)
		self.copying = ActorCopying(self)
		self.output = ActorOutput(self)
		self.holdings = ActorHoldings(self)
		self.payments = ActorPayments(self)
		self.review = ActorReview(self)

	# ---- shared state; subclasses provide storage -------------------------
	@property
	def money(self) -> float:
		raise NotImplementedError

	@money.setter
	def money(self, value: float) -> None:
		raise NotImplementedError

	@property
	def workforce(self) -> Dict[str, float]:
		raise NotImplementedError

	@property
	def knowledge(self) -> Set[str]:
		raise NotImplementedError

	@property
	def concerns(self) -> Set[str]:
		raise NotImplementedError

	@property
	def works(self) -> Dict[str, Dict[str, Any]]:
		raise NotImplementedError

	# ---- what the actor values -------------------------------------------
	def knows(self, node_id: str, world: Any) -> bool:
		return node_id in self.knowledge or node_id in world.knowledge.baseline_knowledge()

	def imitation_worth(self, node_id: str, world: Any) -> float:
		"""Money-equivalent worth to this actor of having the invention."""
		raise NotImplementedError

	def location(self) -> Optional[str]:
		return None

	def sell_output(self, world: Any) -> None:
		"""Put what the actor's concerns make this year into the one goods market, each concern at its own cost."""
		for material in sorted({made for node_id in self.concerns for made in world.enterprises.materials_made_by(node_id)}):
			by_concern = self.output.output_by_concern(material, world)
			world.market.market_sale(self.actor_id, material, sum(tonnes for _node_id, tonnes in by_concern), by_concern)

	def copy_budget(self, world: Any) -> float:
		"""Money it will commit to new copies this year: its purse and what it may still borrow."""
		committed = sum((1.0 - work["progress"]) * (work["money"] + work["labour_cost"])
						for work in self.works.values())
		return max(0.0, self.spendable(world) - committed)

	# ---- imitation --------------------------------------------------------
	def imitation_candidates(self, world: Any) -> List[str]:
		"""The inventions this actor might value, in id order; an actor that
		values only some of them narrows this so it is not scanned in full."""
		return sorted(world.knowledge.demonstrated())

	def research_worth(self, node_id: str, world: Any) -> float:
		"""What researching the node is worth to this actor (0: it does not choose research for itself)."""
		return 0.0

	def research_price(self, costs: Dict[str, Any], node_id: str, world: Any) -> float:
		"""Money the research takes out of its purse: the plan's whole cost."""
		return costs["total"]

	def commit_research(self, node_id: str, costs: Dict[str, Any], world: Any) -> str:
		"""Take the research on as a project in `works`."""
		work = imitation.start_work(node_id, [node_id], costs, world.setting.year)
		work["research"] = True
		self.works[node_id] = work
		return "research begun, %d years" % costs["years"]

	def accept_licence(self, node_id: str, chain: List[str], world: Any) -> None:
		"""Licensed know-how arrives complete: learned, and the actor can make it."""
		self.learn(chain, world)
		self.on_copied(node_id, world)

	def learn(self, chain: List[str], world: Any) -> None:
		self.knowledge.update(chain)

	def on_copied(self, node_id: str, world: Any) -> None:
		"""Hook: what the actor does once it can make the thing."""

	def record_failure(self, node_id: str) -> None:
		"""Hook: bookkeeping after a failed copy."""

	def identity(self) -> str:
		return self.kind

	def act(self, world: Any) -> None:
		"""The actor's own business for the year."""
		self.copying.consider_imitation(world)
		self.copying.work_on_copies(world)
		if self.researches:
			research_choice.decide(self, world)
		self.copying.work_on_research(world)

	def advance(self, world: Any) -> None:
		"""One year: the places it posts are rebuilt by what it does; the labour core hires for them at the clearing."""
		self.staff_wanted.clear()
		self.act(world)


class RecordedActor(Actor):
	"""An actor whose state is one persistent `ActorRecord`."""

	def __init__(self, actor_id: str, record: ActorRecord, policy: Optional[Policy] = None) -> None:
		super().__init__(policy)
		self.stance = RecordedStance(self)
		self.holdings = RecordedHoldings(self)
		self.payments = RecordedPayments(self)
		self.actor_id = actor_id
		self.record = record
		if not record.business.owner_id:
			record.business.business_id = record.business.owner_id = actor_id
		self._purses: Optional[Purses] = None

	def attach(self, purses: Purses) -> None:
		"""Keep the actor's account in `purses`; funds its record was created with are placed there once."""
		self._purses = purses
		if self.record.money:
			funds, self.record.money = self.record.money, 0.0
			self.money = self.money + funds

	@property
	def purses(self) -> Purses:  # type: ignore[override]
		if self._purses is None:
			self.attach(Purses())
		return self._purses  # type: ignore[return-value]

	@property
	def account_id(self) -> str:
		return self.actor_id

	@property
	def money(self) -> float:
		"""The actor's net position: its purse (never below zero) less what it has drawn on its facility."""
		return self.purses.net(self.actor_id)

	@money.setter
	def money(self, value: float) -> None:
		self.purses.set_net(self.actor_id, float(value), "set")

	@property
	def workforce(self) -> Dict[str, float]:
		"""The people the labour core hired for this actor at the last clearing."""
		return self.record.workforce

	@property
	def staff_wanted(self) -> Dict[str, float]:
		"""The places (people by trade) this actor posts to the labour market this year."""
		return self.record.staff_wanted

	@property
	def knowledge(self) -> Set[str]:
		return self.record.knowledge

	@property
	def aware(self) -> Dict[str, int]:
		return self.record.aware

	@property
	def adoption(self) -> Dict[str, Dict[str, Any]]:
		return self.record.adoption

	@property
	def contacts(self) -> Dict[str, float]:
		return self.record.contacts

	def held_tonnes(self, material: str) -> float:
		"""Tonnes of a material or tool the actor itself holds; a start gate counts them before the market."""
		return float(self.record.stores.get(material, 0.0))

	@property
	def business(self) -> Business:
		return self.record.business

	@property
	def concerns(self) -> Set[str]:
		return PlantKeys(self.record.business)

	@property
	def works(self) -> Dict[str, Dict[str, Any]]:
		return self.record.works

	def location(self) -> Optional[str]:
		return self.record.location

	def identity(self) -> str:
		return self.actor_id

	def record_failure(self, node_id: str) -> None:
		self.record.failed_copies[node_id] = self.record.failed_copies.get(node_id, 0) + 1
