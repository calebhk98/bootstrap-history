"""`Actor`: anything that owns money, staff, know-how and works, and decides.

The shared surface is `money`, `workforce`, `knowledge`, `concerns` and
`works`. Subclasses say where that state lives (the founder's household
delegates to the simulation state; a `RecordedActor` keeps an `ActorRecord`)
and what they value. Decisions go through the actor's `decision_policy`.
"""
from typing import Any, Dict, List, Optional, Set

from sim.engine.state import ActorRecord

from . import imitation, ledger
from .borrowing import Borrower
from .ledger import Purpose
from .policy import Decision, Option, Policy, ValuePolicy
from .tuning import ATTENTION_SPAN


class Actor(Borrower):
	kind = "actor"

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

	def output_of(self, material: str, world: Any) -> float:
		"""Tonnes a year of `material` the actor's concerns put on the market."""
		makers = world.concerns_making(material)
		return sum(world.concern_output_tonnes(node_id, material,
											   self.opened_year_of(node_id, world.year),
											   self.staffed_share(node_id) * self.capacity_of(node_id))
				   for node_id in sorted(node_id for node_id in self.concerns if node_id in makers))

	def sell_output(self, world: Any) -> None:
		"""Put what the actor's concerns make this year into the one goods market."""
		for material in sorted({made for node_id in self.concerns for made in world.materials_made_by(node_id)}):
			world.market_sale(self.actor_id, material, self.output_of(material, world))

	def prominence(self) -> float:
		"""How prominent the actor is as a person; a business has none."""
		return 0.0

	def standing(self) -> float:
		"""Standing and patronage that bargain a levy down, 0..1."""
		return 0.0

	def copy_budget(self, world: Any) -> float:
		"""Money it will commit to new copies this year."""
		committed = sum((1.0 - work["progress"]) * (work["money"] + work["labour_cost"])
						for work in self.works.values())
		return max(0.0, self.money - committed)

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
			if worth > 0:
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
		"""One year: act, then press the labour market for the people newly taken on."""
		held = dict(self.workforce)
		self.act(world)
		self.press_new_staff(held, world)

	def press_new_staff(self, held: Dict[str, float], world: Any) -> None:
		"""The labour market feels the people taken on since `held`."""
		for trade, people in sorted(self.workforce.items()):
			added = people - held.get(trade, 0.0)
			if added > 0:
				world.press_labour(trade, added * world.hours_per_person_year)


class RecordedActor(Actor):
	"""An actor whose state is one persistent `ActorRecord`."""

	def __init__(self, actor_id: str, record: ActorRecord, policy: Optional[Policy] = None) -> None:
		super().__init__(policy)
		self.actor_id = actor_id
		self.record = record

	@property
	def money(self) -> float:
		return self.record.money

	@money.setter
	def money(self, value: float) -> None:
		self.record.money = float(value)

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
