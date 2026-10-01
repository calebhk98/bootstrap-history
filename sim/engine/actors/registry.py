"""The set of actors other than the founder's household, and their yearly turn."""
from typing import Any, Dict, List, Optional, Set

from sim.engine.state import ActorRecord, ActorsState

from . import imitation
from .base import RecordedActor
from .firm import Firm
from .government import Government
from .policy import make_policy
from .tuning import ENTREPRENEURIAL_CAPITAL_SHARE, ENTRY_STAKE_BUFFER, VALUE_HORIZON_YEARS

ACTOR_CLASSES = {"firm": Firm, "government": Government}


class _ConcernWatch:
	"""Keeps one firm's entries in the registry's `node -> firm ids` index
	current whenever its concern set changes. Holds only plain data, so a
	state holding watched sets still copies."""

	def __init__(self, firm_id: str, holders: Dict[str, Set[str]], version: List[int]) -> None:
		self.firm_id = firm_id
		self.holders = holders
		self.version = version
		self.known: Set[str] = set()
		self.target: Any = None

	def __call__(self) -> None:
		current = set(self.target)
		if current != self.known:
			self.version[0] += 1
		for node_id in self.known - current:
			self.holders[node_id].discard(self.firm_id)
		for node_id in current - self.known:
			self.holders.setdefault(node_id, set()).add(self.firm_id)
		self.known = current


class ActorRegistry:
	"""Builds actor objects over the persistent records and runs their year."""

	def __init__(self, state: ActorsState) -> None:
		self.state = state
		self.actors: Dict[str, RecordedActor] = {}
		self.world: Any = None
		# which firms hold each concern (kept current by _ConcernWatch), and the ids in order
		self._holders: Dict[str, Set[str]] = {}
		self._ordered_ids: Optional[List[str]] = None
		self._staff: Optional[Dict[str, float]] = None
		# insertion position of each actor (the order supply is summed in), and the ids that are not firms
		self._position: Dict[str, int] = {}
		self._not_firms: Set[str] = set()
		# bumped whenever any firm's concerns change, so market caches keyed on it stay honest
		self.version: List[int] = [0]
		for actor_id in sorted(state.records):
			self._wrap(actor_id)

	def _wrap(self, actor_id: str) -> RecordedActor:
		record = self.state.records[actor_id]
		previous = self.actors.get(actor_id)
		if previous is not None:
			watch = getattr(previous.record.concerns, "_on_change", None)
			if isinstance(watch, _ConcernWatch):
				watch.known, watch.target = set(), ()
				for holding in self._holders.values():
					holding.discard(actor_id)
		actor = ACTOR_CLASSES[record.kind](actor_id, record, make_policy(record.policy_kind))
		if isinstance(actor, Firm):
			actor.rivals_of = self.rivals_of
			from sim.engine.economy import _InvalidatingSet
			watch = _ConcernWatch(actor_id, self._holders, self.version)
			record.concerns = _InvalidatingSet(record.concerns, on_change=watch)
			watch.target = record.concerns
			watch()
		self.actors[actor_id] = actor
		self._position.setdefault(actor_id, len(self._position))
		if isinstance(actor, Firm):
			self._not_firms.discard(actor_id)
		else:
			self._not_firms.add(actor_id)
		self._ordered_ids = None
		self._staff = None
		return actor

	def supply(self, material: str, world: Any) -> float:
		"""Tonnes a year of a material that every recorded actor's concerns put on the market."""
		# only actors that could make it: firms holding a concern that does, and anything not a firm
		ids = set(self._not_firms)
		for node_id in world.concerns_making(material):
			ids.update(self._holders.get(node_id, ()))
		return sum(actor.output_of(material, world)
				   for actor in (self.actors[actor_id] for actor_id in sorted(ids, key=self._position.__getitem__))
				   if not (actor.kind == "firm" and actor.record.exited_year is not None))

	def concerns_in(self, category: str, nodes: Dict[str, Any]) -> int:
		"""Concerns of goods category `category` that actors operate, counted once per operator."""
		return sum(1 for firm in self.active_firms() for node_id in firm.concerns
				   if nodes[node_id].get("cat") == category)

	def refresh_staff(self) -> None:
		"""Forget the staffing tally so the next read counts every actor's workforce again."""
		self._staff = None

	def staff_by_trade(self) -> Dict[str, float]:
		"""People of each trade every recorded actor employs, in full-time equivalents."""
		if self._staff is None:
			totals: Dict[str, float] = {}
			if self._ordered_ids is None:
				self._ordered_ids = sorted(self.actors)
			for actor_id in self._ordered_ids:
				for trade, people in self.actors[actor_id].record.workforce.items():
					totals[trade] = totals.get(trade, 0.0) + people
			self._staff = totals
		return self._staff

	def staff_fte(self, trade: str, excluding: Optional[str] = None) -> float:
		"""People of one trade the actors employ, leaving out one actor's own staff."""
		total = self.staff_by_trade().get(trade, 0.0)
		if excluding is not None and excluding in self.actors:
			total -= self.actors[excluding].workforce.get(trade, 0.0)
		return max(0.0, total)

	def add(self, actor_id: str, record: ActorRecord) -> RecordedActor:
		self.state.records[actor_id] = record
		return self._wrap(actor_id)

	def get(self, actor_id: str) -> Optional[RecordedActor]:
		return self.actors.get(actor_id)

	def of_kind(self, kind: str) -> List[RecordedActor]:
		if self._ordered_ids is None:
			self._ordered_ids = sorted(self.actors)
		return [self.actors[actor_id] for actor_id in self._ordered_ids
				if self.actors[actor_id].kind == kind]

	def ensure_government(self, civ_id: str, name: str = "") -> Government:
		actor_id = "government:" + civ_id
		existing = self.actors.get(actor_id)
		if existing is not None:
			return existing  # type: ignore[return-value]
		return self.add(actor_id, ActorRecord(kind="government", name=name or actor_id))  # type: ignore[return-value]

	def government(self, civ_id: str) -> Government:
		return self.ensure_government(civ_id)

	def active_firms(self) -> List[Firm]:
		return [firm for firm in self.of_kind("firm") if firm.record.exited_year is None]  # type: ignore[misc]

	def rivals_of(self, node_id: str, asking_id: str) -> int:
		"""Other operators sharing the market for a concern, the founder included."""
		operators = self._holders.get(node_id, ())
		count = len(operators) - (1 if asking_id in operators else 0)
		founder_operates = self.world is not None and self.world.is_public(node_id)
		return count + (1 if founder_operates else 0)

	def advance(self, world: Any) -> None:
		self.world = world
		for actor_id in sorted(self.actors):
			actor = self.actors[actor_id]
			if actor.kind == "firm" and actor.record.exited_year is not None:
				continue
			actor.advance(world)
			self.refresh_staff()
		self.consider_entry(world)

	def consider_entry(self, world: Any) -> List[str]:
		"""Found a firm for each proven concern that a new entrant could profit from."""
		self.world = world
		founded = []
		capital_limit = world.society_output() * ENTREPRENEURIAL_CAPITAL_SHARE
		waiting: Dict[str, int] = {}
		for firm in self.active_firms():
			target = firm.record.target
			if target is not None and target not in firm.concerns:
				waiting[target] = waiting.get(target, 0) + 1
		for node_id in world.proven_concerns():
			operators = self.rivals_of(node_id, "") + waiting.get(node_id, 0)
			expected = world.concern_gross(node_id) / (operators + 1.0) - world.upkeep(node_id)
			probe = Firm("probe", ActorRecord(kind="firm"))
			chain = imitation.missing_chain(node_id, world, probe)
			if not chain:
				continue
			plan = imitation.copy_plan(probe, chain, world)
			worth = expected * VALUE_HORIZON_YEARS * imitation.copy_chance(chain, world)
			stake = plan["total"] * ENTRY_STAKE_BUFFER
			if expected <= 0 or worth <= plan["total"] or stake > capital_limit:
				continue
			firm_id = "firm:%d" % (len(self.state.records) + 1)
			founded_firm = self.add(firm_id, ActorRecord(
				kind="firm", name=firm_id, target=node_id,
				last_margin=expected, founded_year=world.year))
			founded_firm.credit(stake, "pooled capital")
			founded.append(firm_id)
		return founded
