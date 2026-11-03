"""The cast: the registry of other actors the module keeps over its saved state, the government of the acting seat's country,
the opening roster, and the world the actors are handed."""
from typing import Any, List, Optional, Tuple

from sim.agents.api import (ActorExtensions, ActorRegistry, cast_from_civilisations, combine_extensions, seed_cast,
                            shipped_extensions)
from sim.assembly.api import Part

from .world import ActorWorld


class Cast(Part):
	def __init__(self, module):
		super().__init__(module)
		self._registry = None   # never saved: rebuilt over the world slot on first use and after a load
		self._extensions = None   # never saved: asked of the providers on first use

	def extensions(self) -> ActorExtensions:
		"""The kinds, founding rules, policies and commands the shipped game and its mods give the actors."""
		if self._extensions is None:
			self._extensions = combine_extensions(self.needs.actor_kinds(), self.needs.actor_spawners(), self.needs.actor_world_scope(),
			                                      self.needs.actor_policies(), self.needs.player_commands())
		return self._extensions

	def shipped_actor_kinds(self) -> dict:
		return shipped_extensions().kinds

	def shipped_actor_spawners(self) -> list:
		return shipped_extensions().spawners

	def shipped_actor_world_scope(self) -> Any:
		return shipped_extensions().world_scope

	def shipped_actor_policies(self) -> dict:
		return shipped_extensions().policies

	def shipped_player_commands(self) -> dict:
		return shipped_extensions().commands

	def provide_declared_kinds(self) -> dict:
		"""The kinds the installed mods declare in data (a body of people with needs and a growth rule)."""
		return self.needs.declared_actor_kinds()

	def cast(self) -> ActorRegistry:
		"""The registry of governments and firms, rebuilt whenever the state object is replaced."""
		state = self.world
		registry = self._registry
		if registry is None or registry.state is not state:
			registry = ActorRegistry(state, self.extensions())
			self._registry = registry
			self.parts.lending.connect_purses()
		return registry

	def follow_tile_transfer(self, command: Any) -> None:
		"""A foreign country's state reads its tiles from its profile: move the tile between the profiles of the countries that
		lost and gained it."""
		self.cast().countries.move_tile_between_countries(command.tile, command.previous, command.to_actor)

	def cast_state(self) -> Any:
		"""The cast's saved records, for readers that look at them without making the registry."""
		return self.world

	def cast_recorded(self) -> bool:
		"""Whether the cast holds any actor's record yet."""
		return bool(self.world.records)

	def government_figures(self, country: str) -> Optional[Tuple[float, float, float]]:
		"""(the grant a patron state pays its clients, the share of income it takes as requisition, as office fees) for the
		government of `country`, or None when it has no record."""
		record = self.world.records.get("government:" + country)
		if record is None:
			return None
		return record.patron_grant, record.levy_requisition_rate, record.levy_office_rate

	def edge(self, name: str) -> Any:
		"""The named edge a posting names when its other side is not an actor the simulation models."""
		return self.world.edge(name)

	def seed_opening_cast(self) -> List[str]:
		"""Seed the roster once, at the game's first actor year; the saved roster stands after that."""
		registry = self.cast()
		if registry.state.home_country:
			return []
		needs = self.needs
		foreign = [needs.civilisation_record[civilization_id] for civilization_id in needs.partners()]
		home_country, entries, profiles = cast_from_civilisations(needs.opening_civilisation(), foreign)
		return seed_cast(registry, home_country, entries, profiles)

	def seeded_actor_registry(self) -> ActorRegistry:
		"""The registry once the civilisation's opening cast is in it (seeding is the first read's side effect)."""
		self.seed_opening_cast()
		return self.cast()

	def state_treasury(self) -> Any:
		"""The government actor of the acting seat's country: the founder's civilisation unless the seat belongs
		to a partner country that has a government of its own in the cast."""
		self.seed_opening_cast()  # a bare record made first would keep the cast from giving it its place and kind
		country = self.needs.acting_country()
		if country is not None:
			government = self.cast().countries.government_of(country)
			if government is not None:
				return government
		civilisation = self.needs.civilisation()
		return self.cast().countries.ensure_government(str(civilisation.get("id")), civilisation.get("name", ""))

	def _actor_world(self) -> ActorWorld:
		parts = self.parts
		return ActorWorld(self.needs, parts.cast, parts.seat_parties, parts.staff)

	def actor_world(self) -> ActorWorld:
		"""What the actors can see and price, with its own table of this turn's shared answers."""
		return self._actor_world()

	def country_world(self, owner: str) -> Any:
		"""The world the owner's state sees (the shared one for the home country, else its country's scope)."""
		return self.cast().countries.world_of_country(owner, self._actor_world())
