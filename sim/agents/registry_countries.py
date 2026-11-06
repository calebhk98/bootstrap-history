"""`RegistryCountries`: which country an actor answers to, which tiles each country holds, and the world each country's actors see.

Reached as `registry.countries`.
"""
from typing import Any, Dict, List, Optional

from . import taxpayer_income
from .government import Government
from .records import ActorRecord


class RegistryCountries:

	def __init__(self, registry: Any) -> None:
		self.registry = registry
		self._tile_owners: Optional[Dict[str, str]] = None   # tile -> country, never saved; `move_tile_between_countries` drops it
		self._scoped: Dict[str, Any] = {}   # country -> the world its actors see this year (rebuilt every `advance`)

	def new_year(self) -> None:
		"""The scoped worlds are rebuilt for the year."""
		self._scoped = {}

	def ensure_government(self, civ_id: str, name: str = "") -> Government:
		actor_id = "government:" + civ_id
		existing = self.registry.actors.get(actor_id)
		if existing is not None:
			return existing  # type: ignore[no-any-return]
		return self.registry.add(actor_id, ActorRecord(kind="government", name=name or actor_id))  # type: ignore[return-value]

	def government(self, civ_id: str) -> Government:
		return self.ensure_government(civ_id)

	def country_of(self, actor: Any) -> str:
		"""The country an actor answers to: its own, else the home country."""
		return actor.record.country or self.registry.state.home_country

	def country_of_tile(self, tile: str) -> Optional[str]:
		"""The country whose profile holds a tile; None when none does."""
		if self._tile_owners is None:
			self._tile_owners = taxpayer_income.tile_owners(self.registry.state.countries)
		return self._tile_owners.get(tile)

	def move_tile_between_countries(self, tile: str, previous: Optional[str], gained_by: Optional[str]) -> None:
		"""Move `tile` between the profiles of the country that lost it and the one that gained it. The only writer of a
		profile's tiles, so it is the one place the remembered tile -> country map is dropped."""
		for country, profile in (self.registry.state.countries or {}).items():
			if country == previous and tile in profile.home_tiles:
				profile.home_tiles.remove(tile)
			if country == gained_by and tile not in profile.home_tiles:
				profile.home_tiles.append(tile)
				profile.home_tiles.sort()
		self._tile_owners = None

	def government_of(self, country: Optional[str]) -> Optional[Government]:
		"""The government of a country (the home country for None), if it has one."""
		state = self.registry.state
		return self.registry.actors.get("government:" + str(country or state.home_country))  # type: ignore[return-value]

	def world_for(self, actor: Any, world: Any) -> Any:
		"""The world an actor sees: the shared one for the home country, else its country's scope."""
		return self.world_of_country(self.country_of(actor), world)

	def world_of_country(self, country: Optional[str], world: Any) -> Any:
		"""The world a country's actors see: the shared one for the home country, else the country's scope."""
		state = self.registry.state
		scope = self.registry.extensions.world_scope
		if scope is None or not country or country == state.home_country or country not in state.countries:
			return world
		scoped = self._scoped.get(country)
		if scoped is None:
			scoped = scope(world, state.countries[country], self.registry)
			self._scoped[country] = scoped
		return scoped

	def home_actors(self, kind: str) -> List[Any]:
		"""The actors of a kind that answer to the home country, in id order."""
		home = self.registry.state.home_country
		return [actor for actor in self.registry.of_kind(kind) if self.country_of(actor) == home]
