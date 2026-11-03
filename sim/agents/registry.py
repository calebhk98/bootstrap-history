"""The set of actors other than the founder's household, and their yearly turn."""
from bisect import insort
from typing import Any, Dict, List, Optional

from .records import ActorRecord, ActorsState

from .base import RecordedActor
from .entry_round import NicheEntry
from .extensions import ActorExtensions
from . import adoption, awareness, patent_index, research
from .group import InterestGroup
from .policy import make_policy
from .registry_concerns import RegistryConcerns
from .registry_countries import RegistryCountries
from .registry_staff import RegistryStaff
from .tuning import ENTREPRENEURIAL_CAPITAL_SHARE


class ActorRegistry:
	"""Builds actor objects over the persistent records and runs their year."""

	def __init__(self, state: ActorsState, extensions: Optional[ActorExtensions] = None) -> None:
		self.state = state
		if extensions is None:   # a registry made outside a game holds what the game ships
			from .shipped import shipped_extensions
			extensions = shipped_extensions()
		self.extensions = extensions
		self.actors: Dict[str, RecordedActor] = {}
		self.world: Any = None
		self.ordered_ids: Optional[List[str]] = None
		self.patent_index = patent_index.PatentIndex()
		# of_kind answers, in id order: a new actor joins its kind's list, a replaced actor drops them all
		self._by_kind: Dict[str, List[Any]] = {}
		self._by_kind_count = 0
		self._bans: Optional[Dict[str, str]] = None
		# node -> (year, cost): what researching it cost when last worked out (see ActorWorld.research.research_cost)
		self.research_costs: Dict[str, Any] = {}
		self.staff = RegistryStaff(self)
		self.concerns = RegistryConcerns(self)
		self.countries = RegistryCountries(self)
		for actor_id in sorted(state.records):
			self._wrap(actor_id)

	def _wrap(self, actor_id: str) -> RecordedActor:
		record = self.state.records[actor_id]
		previous = self.actors.get(actor_id)
		if previous is not None:
			self.concerns.forget(actor_id, previous)
		if record.kind not in self.extensions.kinds:
			owner = record.kind.partition(":")[0] if ":" in record.kind else ""
			raise ValueError("actor %s is of kind %r, which is not registered%s" % (
				actor_id, record.kind, "; it comes from mod %s, which is not installed or whose code is not allowed" % owner
				if owner else ""))
		actor = self.extensions.kinds[record.kind](actor_id, record, make_policy(record.policy_kind, self.extensions.policies))
		actor.attach(self.state.purses)
		self.concerns.hook(actor)
		patent_index.track(record, previous is not None)
		self.actors[actor_id] = actor
		prior_order = self.ordered_ids
		self.ordered_ids = None
		if previous is None and self._by_kind_count == len(self.actors) - 1:
			if actor.kind in self._by_kind:
				insort(self._by_kind[actor.kind], actor, key=lambda each: each.actor_id)
			self._by_kind_count = len(self.actors)
		else:
			self._by_kind = {}
		self.staff.actor_added(actor_id, prior_order, previous is None)
		self._bans = None
		return actor

	def add(self, actor_id: str, record: ActorRecord) -> RecordedActor:
		self.state.records[actor_id] = record
		return self._wrap(actor_id)

	def get(self, actor_id: str) -> Optional[RecordedActor]:
		return self.actors.get(actor_id)

	def of_kind(self, kind: str) -> List[RecordedActor]:
		if self.ordered_ids is None:
			self.ordered_ids = sorted(self.actors)
		if self._by_kind_count != len(self.actors):
			self._by_kind, self._by_kind_count = {}, len(self.actors)
		if kind not in self._by_kind:
			self._by_kind[kind] = [self.actors[actor_id] for actor_id in self.ordered_ids
								   if self.actors[actor_id].kind == kind]
		return list(self._by_kind[kind])

	def government_of(self, country: Optional[str]) -> Any:
		"""Forwarder for sim/markets (not yet moved to `countries`)."""
		return self.countries.government_of(country)

	def ensure_government(self, civ_id: str, name: str = "") -> Any:
		"""Forwarder for sim/markets (not yet moved to `countries`)."""
		return self.countries.ensure_government(civ_id, name)

	def sorted_ids(self) -> List[str]:
		if self.ordered_ids is None:
			self.ordered_ids = sorted(self.actors)
		return self.ordered_ids

	def purse_lenders(self) -> List[RecordedActor]:
		"""Actors in play whose class sets `lends_from_purse`, in id order: the credit market offers their purses to borrowers."""
		return [self.actors[actor_id] for actor_id in sorted(self.actors)
				if getattr(self.actors[actor_id], "lends_from_purse", False) and self.actors[actor_id].record.exited_year is None]

	def patent_holders(self, node_id: str) -> List[RecordedActor]:
		"""The actors whose patents name the node (see patent_index.py); each may have let it expire."""
		return list(self.patent_index.holders_of(self.actors, node_id))

	def _seat_in_id_order(self) -> None:
		"""Hold the actors and their records in id order, as a load builds them, so a sweep over either matches a loaded game."""
		for store in (self.actors, self.state.records):
			if list(store) != sorted(store):
				held = [(key, store[key]) for key in sorted(store)]
				store.clear()
				store.update(held)

	def advance(self, world: Any) -> None:
		self.world = world
		self.countries.new_year()
		self._seat_in_id_order()
		first = True
		before = self.staff.workforces()
		for actor_id in sorted(self.actors):
			actor = self.actors[actor_id]
			world.market.market_forget(actor_id)
			if actor.record.exited_year is not None:
				continue
			self.staff.begin_turn(actor)
			seen = self.countries.world_for(actor, world)
			actor.advance(seen)
			actor.sell_output(seen)
			self.staff.end_turn(actor, first)
			first = False
		self.staff.stop_turns()
		researchers = [actor for actor in self.actors.values() if actor.researches and actor.record.exited_year is None]
		awareness.spread(researchers, world)
		research.diffuse(researchers, world)
		for actor in sorted(researchers, key=lambda each: each.identity()):
			adoption.advance_actor(actor, self.countries.world_for(actor, world))
		for _name, spawner in list(self.extensions.spawners):
			spawner(self, world)
		self.staff.end_year(before)
		self._bans = None

	def consider_entry(self, world: Any) -> List[str]:
		"""Found firms into each proven concern for as long as its market still pays an entrant, after
		its own output and that of entrants already waiting reaches the market and after what a firm
		carries, more than the capital it ties up would earn at the market's rate."""
		self.world = world
		founded = []
		pool = [world.revenue.society_output() * ENTREPRENEURIAL_CAPITAL_SHARE]
		waiting: Dict[str, int] = {}
		for firm in self.concerns.active_firms():
			target = firm.record.target
			if target is not None and target not in firm.concerns:
				key = world.market.market_key(target)
				waiting[key] = waiting.get(key, 0) + 1
		strata_exist = bool(self.of_kind("stratum"))
		for node_id in self.concerns.proven_concerns(world):
			key = world.market.market_key(node_id)
			niche = NicheEntry(self, world, node_id, pool, strata_exist)
			while True:
				firm_id = niche.found(self.concerns.rivals_of(node_id, ""), waiting.get(key, 0))
				if firm_id is None:
					break
				waiting[key] = waiting.get(key, 0) + 1
				founded.append(firm_id)
		return founded

	def consider_groups(self, world: Any) -> List[str]:
		"""Organise a group for each body of people, in each country, whose lost income has reached the point at
		which they act on their state, and call a dissolved group back when its cause returns."""
		formed: List[str] = []
		home = self.state.home_country
		for country in [home] + sorted(set(self.state.countries) - {home}):
			if country != home and self.countries.government_of(country) is None:
				continue
			formed.extend(self._organise_groups(self.countries.world_of_country(country, world), country))
		return formed

	def _organise_groups(self, world: Any, country: str) -> List[str]:
		"""The groups of one country's sectors, read through that country's world."""
		from .group_tuning import GROUP_ORGANISING_WEIGHT
		home = country == self.state.home_country
		formed = []
		for key, sector in sorted(world.groups.sectors().items()):
			if sector.lost_income / world.groups.scope_revenue(sector.scope) < GROUP_ORGANISING_WEIGHT:
				continue
			group_id = "group:" + key if home else "group:%s:%s" % (country, key)
			existing = self.actors.get(group_id)
			if existing is not None and existing.record.exited_year is None:
				continue
			if existing is None:
				existing = self.add(group_id, ActorRecord(**InterestGroup.founded_by(sector, None if home else country),
														  founded_year=world.setting.year))
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
			self._bans = {group.record.subject: group.record.name for group in self.countries.home_actors("interest_group")
						  if group.record.exited_year is None and group.record.demands and not group.record.technique}
		return self._bans
