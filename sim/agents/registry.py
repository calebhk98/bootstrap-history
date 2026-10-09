"""The set of actors other than the founder's household, and their yearly turn."""
from bisect import bisect_left
from itertools import accumulate
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .records import ActorRecord, ActorsState

from .base import RecordedActor
from .concern_totals import ConcernTotals
from .entry_round import NicheEntry
from .firm import Firm
from .government import Government
from .group import InterestGroup
from .policy import make_policy
from .tuning import ENTREPRENEURIAL_CAPITAL_SHARE

# kind -> class; `register_actor_kind` adds to it, so a mod can bring its own kind of actor
ACTOR_CLASSES: Dict[str, Any] = {"firm": Firm, "government": Government, "interest_group": InterestGroup}

# what founds new actors after every actor has had its year, in the order registered: (name, spawner),
# each spawner a function (registry, world) -> ids of the actors it founded
SPAWNERS: List[Tuple[str, Callable[["ActorRegistry", Any], List[str]]]] = []

# builds the world an actor of another country sees from the shared world, that country's profile
# and the registry; None until a scope is registered, when every actor sees the shared world
WORLD_SCOPE: List[Optional[Callable[[Any, Any, "ActorRegistry"], Any]]] = [None]


def register_actor_kind(kind: str, actor_class: Any) -> None:
	"""Make records of `kind` build `actor_class` objects."""
	ACTOR_CLASSES[kind] = actor_class


def register_spawner(name: str, spawner: Callable[["ActorRegistry", Any], List[str]]) -> None:
	"""Run `spawner` every year after the actors' turns; registering a name again replaces it."""
	for index, (existing, _old) in enumerate(SPAWNERS):
		if existing == name:
			SPAWNERS[index] = (name, spawner)
			return
	SPAWNERS.append((name, spawner))


def register_world_scope(scope: Callable[[Any, Any, "ActorRegistry"], Any]) -> None:
	"""`scope(world, profile, registry)` is the world an actor of the country `profile` sees."""
	WORLD_SCOPE[0] = scope


class _ConcernWatch:
	"""Keeps one firm's entries in the registry's `node -> firm ids` index
	current whenever its concern set changes. Holds only plain data, so a
	state holding watched sets still copies."""

	def __init__(self, firm_id: str, holders: Dict[str, Set[str]], version: List[int],
				 totals: ConcernTotals, record: Any) -> None:
		self.firm_id = firm_id
		self.holders = holders
		self.version = version
		self.totals = totals
		self.record = record
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
		self.totals.sync(self.firm_id, self.record)


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
		# per trade, every actor's staff in id order and the running left-to-right sum of it, kept
		# current by re-summing from the one actor whose staff changed (see `_staff_total`)
		self._columns: Dict[str, Any] = {}
		self._column_position: Dict[str, int] = {}
		self._changed_actors: Set[str] = set()
		self._columns_synced = False
		self._acting: Optional[RecordedActor] = None
		self._staff_basis: Dict[str, float] = {}
		self._bans: Optional[Dict[str, str]] = None
		# bumped whenever any firm's concerns change, so market caches keyed on it stay honest
		self.version: List[int] = [0]
		self._totals = ConcernTotals()
		# country -> the world its actors see this year (rebuilt every `advance`)
		self._scoped: Dict[str, Any] = {}
		for actor_id in sorted(state.records):
			self._wrap(actor_id)

	def _wrap(self, actor_id: str) -> RecordedActor:
		record = self.state.records[actor_id]
		previous = self.actors.get(actor_id)
		if previous is not None:
			watch = getattr(previous.record.concerns, "_on_change", None)
			if isinstance(watch, _ConcernWatch):
				watch.known, watch.target = set(), ()
				self._totals.forget(actor_id)
				for holding in self._holders.values():
					holding.discard(actor_id)
		if record.kind not in ACTOR_CLASSES:
			owner = record.kind.partition(":")[0] if ":" in record.kind else ""
			raise ValueError("actor %s is of kind %r, which is not registered%s" % (
				actor_id, record.kind, "; it comes from mod %s, which is not installed or whose code is not allowed" % owner
				if owner else ""))
		actor = ACTOR_CLASSES[record.kind](actor_id, record, make_policy(record.policy_kind))
		if hasattr(type(actor), "rivals_of"):
			# an actor that runs concerns in the shared market: it counts its rivals and is counted as one
			actor.rivals_of = self.rivals_of
			if hasattr(type(actor), "on_capacity_change"):
				actor.on_capacity_change = self.note_capacity_change
			if hasattr(type(actor), "find_actor"):
				actor.find_actor = self.get
			from sim.invalidating import _InvalidatingSet
			watch = _ConcernWatch(actor_id, self._holders, self.version, self._totals, record)
			record.concerns = _InvalidatingSet(record.concerns, on_change=watch)
			watch.target = record.concerns
			watch()
		self.actors[actor_id] = actor
		prior_order = self._ordered_ids
		self._ordered_ids = None
		if previous is None and self._columns and prior_order is not None and len(prior_order) == len(self.actors) - 1:
			self._insert_into_columns(actor_id, prior_order)
		else:
			self.refresh_staff()
		self._bans = None
		return actor

	def note_capacity_change(self, firm_id: str) -> None:
		"""A firm has changed the size it runs a concern at: the totals take its new sizes."""
		self.version[0] += 1
		self._totals.sync(firm_id, self.actors[firm_id].record)

	def capacity_in(self, node_id: str) -> float:
		"""Founding sizes of one concern that every active firm runs, summed."""
		return self._totals.size_by_node.get(node_id, 0.0)

	def concerns_in(self, category: str, nodes: Dict[str, Any]) -> float:
		"""Founding sizes of concerns of goods category `category` that actors operate, summed over operators."""
		return self._totals.size_of_category(category, nodes)

	def refresh_staff(self) -> None:
		"""Forget the staffing and demand tallies so the next read counts every actor again."""
		self._staff = None
		self._columns = {}
		self._changed_actors = set()
		self._columns_synced = False

	def _staff_total(self, trade: str) -> float:
		"""People of one trade across every actor, summed left to right in actor-id order, as
		`staff_by_trade` sums them, but as of the same moments: the actors' staff as read at the
		first count after a change, the acting actor's as it stood then."""
		acting = self._acting
		if not self._columns_synced:
			if acting is not None:
				self._staff_basis = dict(acting.workforce)
			changed = self._changed_actors
			if acting is not None:
				changed = changed | {acting.actor_id}
			for actor_id in changed:
				self._resum_actor(actor_id)
			self._changed_actors = set()
			self._columns_synced = True
		column = self._columns.get(trade)
		if column is None:
			if self._ordered_ids is None:
				self._ordered_ids = sorted(self.actors)
			self._current_positions()
			values = [self.actors[actor_id].record.workforce.get(trade, 0.0) for actor_id in self._ordered_ids]
			if acting is not None:
				values[self._column_position[acting.actor_id]] = self._staff_basis.get(trade, 0.0)
			column = self._columns[trade] = (values, list(accumulate(values, initial=0.0)))
		return column[1][-1]

	def _current_positions(self) -> None:
		"""Make `_column_position` match the actor-id order."""
		if self._ordered_ids is None:
			self._ordered_ids = sorted(self.actors)
		if len(self._column_position) != len(self._ordered_ids):
			self._column_position = {actor_id: place for place, actor_id in enumerate(self._ordered_ids)}

	def _insert_into_columns(self, actor_id: str, order: List[str]) -> None:
		"""Add one new actor to the id order and to every counted trade's column, re-summing
		from its place; the next count then re-reads the acting actor's staff."""
		place = bisect_left(order, actor_id)
		order.insert(place, actor_id)
		self._ordered_ids = order
		self._column_position = {}
		staff = self.actors[actor_id].record.workforce
		for trade, (values, running) in self._columns.items():
			values.insert(place, staff.get(trade, 0.0))
			running[place + 1:] = list(accumulate(values[place:], initial=running[place]))[1:]
		self._staff = None
		self._columns_synced = False

	def _resum_actor(self, actor_id: str) -> None:
		"""Bring every counted trade's column up to the actor's present staff."""
		actor = self.actors.get(actor_id)
		self._current_positions()
		place = self._column_position.get(actor_id)
		if actor is None or place is None:
			self._columns = {}
			return
		staff = actor.record.workforce
		for trade, (values, running) in self._columns.items():
			people = staff.get(trade, 0.0)
			if people != values[place]:
				values[place] = people
				running[place + 1:] = list(accumulate(values[place:], initial=running[place]))[1:]

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
			if self._acting is not None:
				self._staff_basis = dict(self._acting.workforce)
		return self._staff

	def staff_fte(self, trade: str, excluding: Optional[str] = None) -> float:
		"""People of one trade the actors employ, leaving out one actor's own staff."""
		total = self._staff_total(trade)
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

	def country_of(self, actor: Any) -> str:
		"""The country an actor answers to: its own, else the home country."""
		record = getattr(actor, "record", None)
		country = None if record is None else record.country
		return country or self.state.home_country

	def government_of(self, country: Optional[str]) -> Optional[Government]:
		"""The government of a country (the home country for None), if it has one."""
		return self.actors.get("government:" + str(country or self.state.home_country))  # type: ignore[return-value]

	def world_for(self, actor: Any, world: Any) -> Any:
		"""The world an actor sees: the shared one for the home country, else its country's scope."""
		country = self.country_of(actor)
		scope = WORLD_SCOPE[0]
		if scope is None or not country or country == self.state.home_country or country not in self.state.countries:
			return world
		scoped = self._scoped.get(country)
		if scoped is None:
			scoped = scope(world, self.state.countries[country], self)
			self._scoped[country] = scoped
		return scoped

	def market_operators(self) -> List[RecordedActor]:
		"""Every actor still in business that runs concerns in the shared market: firms and players."""
		return [actor for actor in (self.actors[actor_id] for actor_id in self._sorted_ids())
				if hasattr(type(actor), "rivals_of") and actor.record.exited_year is None]

	def _sorted_ids(self) -> List[str]:
		if self._ordered_ids is None:
			self._ordered_ids = sorted(self.actors)
		return self._ordered_ids

	def proven_concerns(self, world: Any) -> List[str]:
		"""Concerns some player has shown to pay, the founder's and every player actor's, in id order."""
		proven = set(world.proven_concerns())
		for actor in self.actors.values():
			shown = getattr(actor, "proven_concerns", None)
			if shown is not None and actor.record.exited_year is None:
				proven.update(shown(world))
		return sorted(proven)

	def active_firms(self) -> List[Firm]:
		return [firm for firm in self.of_kind("firm") if firm.record.exited_year is None]  # type: ignore[misc]

	def rivals_of(self, node_id: str, asking_id: str) -> float:
		"""Founding sizes of the concern that other operators run in its market, the founder's included."""
		operators = self._holders.get(node_id, ())
		count = self.capacity_in(node_id)
		if asking_id in operators:
			count -= self.actors[asking_id].record.capacity.get(node_id, 1.0)
		founder_operates = self.world is not None and self.world.is_public(node_id)
		return count + (1 if founder_operates else 0)

	def _workforces(self) -> Dict[str, Dict[str, float]]:
		return {actor_id: dict(actor.workforce) for actor_id, actor in self.actors.items()}

	def advance(self, world: Any) -> None:
		self.world = world
		self._scoped = {}
		first = True
		before = self._workforces()
		for actor_id in sorted(self.actors):
			actor = self.actors[actor_id]
			world.market_forget(actor_id)
			if actor.record.exited_year is not None:
				continue
			# the tally is a count of everyone's staff as of the acting actor's staff in `_staff_basis`
			self._acting, self._staff_basis = actor, dict(actor.workforce)
			seen = self.world_for(actor, world)
			actor.advance(seen)
			actor.sell_output(seen)
			# it stays when the acting actor's staff is what the count saw; the first actor of a
			# year always recounts, since anything between years is unseen
			if first:
				self.refresh_staff()
			elif actor.workforce != self._staff_basis:
				self._staff = None
				self._changed_actors.add(actor.actor_id)
				self._columns_synced = False
			first = False
		self._acting = None
		for _name, spawner in list(SPAWNERS):
			spawner(self, world)
		# entry and group formation change staff after the last count; whatever reads before the next
		# year's first actor (the founder's own turn) sees what is there, as a reloaded game does.
		# A year in which no actor's staff differs from the year's start leaves the tally standing.
		if self._workforces() != before:
			self.refresh_staff()
		self._bans = None

	def consider_entry(self, world: Any) -> List[str]:
		"""Found firms into each proven concern for as long as its market still pays an entrant, after
		its own output and that of entrants already waiting reaches the market and after what a firm
		carries, more than the capital it ties up would earn at the market's rate."""
		self.world = world
		founded = []
		pool = [world.society_output() * ENTREPRENEURIAL_CAPITAL_SHARE]
		waiting: Dict[str, int] = {}
		for firm in self.active_firms():
			target = firm.record.target
			if target is not None and target not in firm.concerns:
				key = world.market_key(target)
				waiting[key] = waiting.get(key, 0) + 1
		strata_exist = bool(self.of_kind("stratum"))
		for node_id in self.proven_concerns(world):
			key = world.market_key(node_id)
			niche = NicheEntry(self, world, node_id, pool, strata_exist)
			while True:
				firm_id = niche.found(self.rivals_of(node_id, ""), waiting.get(key, 0))
				if firm_id is None:
					break
				waiting[key] = waiting.get(key, 0) + 1
				founded.append(firm_id)
		return founded

	def consider_groups(self, world: Any) -> List[str]:
		"""Organise a group for each body of people whose lost income has reached the point at
		which they act on the state, and call a dissolved group back when its cause returns."""
		from .group_tuning import GROUP_ORGANISING_WEIGHT
		formed = []
		for key, sector in sorted(world.sectors().items()):
			if sector.lost_income / world.scope_revenue(sector.scope) < GROUP_ORGANISING_WEIGHT:
				continue
			group_id = "group:" + key
			existing = self.actors.get(group_id)
			if existing is not None and existing.record.exited_year is None:
				continue
			if existing is None:
				existing = self.add(group_id, ActorRecord(**InterestGroup.founded_by(sector), founded_year=world.year))
			else:
				existing.record.exited_year = None
			existing.record.lost_income = 0.0
			existing.advance(world)
			formed.append(group_id)
		return formed

	def prohibitions(self) -> Dict[str, str]:
		"""Commodity -> name of the interest group whose demand to forbid the techniques that
		make it the state is meeting this year."""
		if self._bans is None:
			self._bans = {group.record.subject: group.record.name for group in self.of_kind("interest_group")
						  if group.record.exited_year is None and group.record.demands}
		return self._bans


register_spawner("firm_entry", lambda registry, world: registry.consider_entry(world))
register_spawner("interest_groups", lambda registry, world: registry.consider_groups(world))
