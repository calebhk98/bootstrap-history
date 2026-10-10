"""`Actor`: anything that owns money, staff, know-how and works, and decides.

The shared surface is `money`, `workforce`, `knowledge`, `concerns` and
`works`. Subclasses say where that state lives (the founder's household
delegates to the simulation state; a `RecordedActor` keeps an `ActorRecord`)
and what they value. Decisions go through the actor's `decision_policy`.
"""
from typing import Any, Dict, List, Optional, Set, Tuple

from .records import ActorRecord

from . import imitation, ledger
from .borrowing import Borrower
from .ledger import Purpose
from .purses import EDGE_OUTSIDE, Purses
from .policy import Decision, Option, Policy, ValuePolicy
from .tuning import ATTENTION_SPAN


class Actor(Borrower):
	kind = "actor"
	purses: Any = None   # the book of purses the actor keeps its account in, when it keeps one

	def __init__(self, policy: Optional[Policy] = None) -> None:
		self.decision_policy = policy or ValuePolicy()

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

	# ---- moving money -----------------------------------------------------
	def credit(self, amount: float, purpose: Purpose) -> None:
		"""Money in, with the purpose it came for."""
		self.money += amount
		self.note_income(purpose, amount)

	def debit(self, amount: float, purpose: Purpose) -> None:
		"""Money out, with the purpose it went for."""
		self.money -= amount
		self.note_outlay(purpose, amount)

	def note_income(self, purpose: Purpose, amount: float) -> None:
		"""Hook: an actor with books records what came in."""

	def note_outlay(self, purpose: Purpose, amount: float) -> None:
		"""Hook: an actor with books records what went out."""

	# ---- what the actor values -------------------------------------------
	def knows(self, node_id: str, world: Any) -> bool:
		return node_id in self.knowledge or node_id in world.baseline_knowledge()

	def imitation_worth(self, node_id: str, world: Any) -> float:
		"""Money-equivalent worth to this actor of having the invention."""
		raise NotImplementedError

	def location(self) -> Optional[str]:
		return None

	def opened_year_of(self, node_id: str, default: int) -> int:
		"""When the actor began running a concern."""
		return default

	def staffed_share(self, node_id: str) -> float:
		"""Share of a concern's staff the actor has found."""
		return 1.0

	def capacity_of(self, node_id: str) -> float:
		"""How many times its founding size the actor runs a concern at."""
		return 1.0

	def output_by_concern(self, material: str, world: Any) -> List[Tuple[str, float]]:
		"""[(node id, tonnes a year)] of `material` each of the actor's concerns puts on the market."""
		makers = world.concerns_making(material)
		return [(node_id, world.concern_output_tonnes(node_id, material,
													  self.opened_year_of(node_id, world.year),
													  self.staffed_share(node_id) * self.capacity_of(node_id)))
				for node_id in sorted(node_id for node_id in self.concerns if node_id in makers)]

	def output_of(self, material: str, world: Any) -> float:
		"""Tonnes a year of `material` the actor's concerns put on the market."""
		return sum(tonnes for _node_id, tonnes in self.output_by_concern(material, world))

	def sell_output(self, world: Any) -> None:
		"""Put what the actor's concerns make this year into the one goods market, each concern at its own cost."""
		for material in sorted({made for node_id in self.concerns for made in world.materials_made_by(node_id)}):
			by_concern = self.output_by_concern(material, world)
			world.market_sale(self.actor_id, material, sum(tonnes for _node_id, tonnes in by_concern), by_concern)

	def prominence(self) -> float:
		"""How prominent the actor is as a person; a business has none."""
		return 0.0

	def standing(self) -> float:
		"""Standing and patronage that bargain a levy down, 0..1."""
		return 0.0

	def demand_stance(self) -> str:
		"""How the actor answers the state's demands: comply unless it has said otherwise."""
		return "comply"

	def set_demand_stance(self, stance: str) -> None:
		"""Answer the state's demands from now on with `stance`."""
		raise NotImplementedError

	def service_worth(self) -> float:
		"""Money's worth of service the actor will offer the state in place of part of a demand."""
		return 0.0

	def concealed_wealth(self) -> float:
		"""Wealth the actor holds where the state cannot count it."""
		return 0.0

	def defiance(self) -> float:
		"""0..1: how far the state holds the actor's refusals against it."""
		return 0.0

	def set_concealed_wealth(self, amount: float) -> None:
		"""Hold `amount` of its wealth out of the state's sight."""

	def set_defiance(self, level: float) -> None:
		"""The state now holds the actor's defiance at `level`."""

	def copy_budget(self, world: Any) -> float:
		"""Money it will commit to new copies this year: its purse and what it may still borrow."""
		committed = sum((1.0 - work["progress"]) * (work["money"] + work["labour_cost"])
						for work in self.works.values())
		return max(0.0, self.spendable(world) - committed)

	# ---- imitation --------------------------------------------------------
	def imitation_candidates(self, world: Any) -> List[str]:
		"""The inventions this actor might value, in id order; an actor that
		values only some of them narrows this so it is not scanned in full."""
		return world.founder_inventions()

	def imitation_options(self, world: Any) -> List[Option]:
		"""Priced options for the inventions that look most worth copying."""
		candidates = []
		known = self.knowledge
		baseline = world.baseline_knowledge()
		for node_id in self.imitation_candidates(world):
			if node_id in known or node_id in baseline or node_id in self.works:
				continue
			worth = self.imitation_worth(node_id, world)
			if worth > 0 and imitation.in_sight(self.location(), node_id, world):
				candidates.append((worth * world.exposure(node_id, self.location()), node_id))
		candidates.sort(key=lambda item: (-item[0], item[1]))
		options = []
		for worth, node_id in candidates[:ATTENTION_SPAN]:
			chain = imitation.missing_chain(node_id, world, self)
			if not chain:
				continue
			plan = imitation.copy_plan(self, chain, world)
			options.append(Option(subject=node_id, worth=worth, cost=plan["total"],
								  chance=imitation.copy_chance(chain, world),
								  detail={"chain": chain, "plan": plan}))
		return options

	def consider_imitation(self, world: Any) -> List[str]:
		"""Ask the policy which invention to copy, and begin those copies."""
		options = self.imitation_options(world)
		if not options:
			return []
		decision = Decision("imitate", options, self.copy_budget(world))
		begun = []
		for option in self.decision_policy.choose(self, decision):
			detail = option.detail
			self.works[option.subject] = imitation.start_work(
				option.subject, detail["chain"], detail["plan"], world.year)
			begun.append(option.subject)
		return begun

	def work_on_copies(self, world: Any) -> List[str]:
		"""Advance every copy a year; returns the ids that succeeded."""
		self.workforce.clear()
		finished = []
		for node_id in sorted(self.works):
			work = self.works[node_id]
			if not imitation.work_year(self, node_id, work, world):
				continue
			del self.works[node_id]
			roll = world.rng_for(world.year, self.kind, node_id, self.identity())
			if roll.random() < imitation.copy_chance(work["chain"], world):
				self.learn(work["chain"], world)
				self.on_copied(node_id, world)
				finished.append(node_id)
			else:
				self.record_failure(node_id)
		return finished

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
		self.consider_imitation(world)
		self.work_on_copies(world)

	def advance(self, world: Any) -> None:
		"""One year: act, then press the labour market for the people newly taken on and ease it for those let go."""
		held = dict(self.workforce)
		self.act(world)
		self.press_new_staff(held, world)

	def press_new_staff(self, held: Dict[str, float], world: Any) -> None:
		"""The labour market feels the people taken on since `held` and eases for those let go."""
		for trade, people in sorted(self.workforce.items()):
			added = people - held.get(trade, 0.0)
			if added > 0:
				world.labour_market.hire(self, trade, added * world.hours_per_person_year)
		for trade, people in sorted(held.items()):
			shed = people - self.workforce.get(trade, 0.0)
			if shed > 0:
				world.labour_market.release(self, trade, shed * world.hours_per_person_year)


class RecordedActor(Actor):
	"""An actor whose state is one persistent `ActorRecord`."""

	def __init__(self, actor_id: str, record: ActorRecord, policy: Optional[Policy] = None) -> None:
		super().__init__(policy)
		self.actor_id = actor_id
		self.record = record
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

	def credit(self, amount: float, purpose: Purpose) -> None:
		self.purses.transfer(EDGE_OUTSIDE, self.actor_id, amount, ledger.purposes_label(purpose))
		self.note_income(purpose, amount)

	def debit(self, amount: float, purpose: Purpose) -> None:
		self.purses.transfer(self.actor_id, EDGE_OUTSIDE, amount, ledger.purposes_label(purpose))
		self.note_outlay(purpose, amount)

	@property
	def workforce(self) -> Dict[str, float]:
		return self.record.workforce

	@property
	def knowledge(self) -> Set[str]:
		return self.record.knowledge

	@property
	def concerns(self) -> Set[str]:
		return self.record.concerns

	@property
	def works(self) -> Dict[str, Dict[str, Any]]:
		return self.record.works

	def location(self) -> Optional[str]:
		return self.record.location

	def demand_stance(self) -> str:
		return self.record.demand_stance

	def set_demand_stance(self, stance: str) -> None:
		self.record.demand_stance = stance

	def service_worth(self) -> float:
		return self.record.service_offer

	def concealed_wealth(self) -> float:
		return self.record.concealed

	def defiance(self) -> float:
		return self.record.defiance

	def set_concealed_wealth(self, amount: float) -> None:
		self.record.concealed = max(0.0, amount)

	def set_defiance(self, level: float) -> None:
		self.record.defiance = level

	def opened_year_of(self, node_id: str, default: int) -> int:
		return self.record.opened_year.get(node_id, default)

	def staffed_share(self, node_id: str) -> float:
		return self.record.staffing.get(node_id, 1.0)

	def capacity_of(self, node_id: str) -> float:
		return self.record.capacity.get(node_id, 1.0)

	def note_income(self, purpose: Purpose, amount: float) -> None:
		for label, part in ledger.parts(purpose, amount).items():
			self.record.income[label] = self.record.income.get(label, 0.0) + part

	def note_outlay(self, purpose: Purpose, amount: float) -> None:
		for label, part in ledger.parts(purpose, amount).items():
			self.record.outlays[label] = self.record.outlays.get(label, 0.0) + part

	def identity(self) -> str:
		return self.actor_id

	def record_failure(self, node_id: str) -> None:
		self.record.failed_copies[node_id] = self.record.failed_copies.get(node_id, 0) + 1
