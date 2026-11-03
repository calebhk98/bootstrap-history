"""The cast's answers about countries, treasuries and the people of the home country, mixed into `Actors`."""
from typing import Any, Dict, FrozenSet, List, Tuple

from sim.agents.api import tax_burden
from sim.assembly.api import Part

from . import country_rules


class CountryViews(Part):
	"""Needs: civilisation, seat_list."""


	def has_state(self, owner: str) -> bool:
		return country_rules.is_country_with_state(owner, str(self.needs.civilisation()["id"]), self.parts.cast.cast().state.countries)

	def countries(self) -> List[str]:
		return list(self.parts.cast.cast().state.countries)

	def organised_factions(self, owner: str) -> List[Tuple[float, float]]:
		return country_rules.organised_factions(self.parts.cast.cast().of_kind("interest_group"), str(self.needs.civilisation()["id"]), owner)

	def home_country(self) -> Dict[str, Any]:
		state = self.parts.cast.cast().state
		return country_rules.home_country_facts(state.home_country, state.countries)

	def state_knowledge(self) -> FrozenSet[str]:
		"""The nodes the home government holds."""
		return frozenset(self.parts.cast.state_treasury().knowledge)

	def holder_treasury(self, holder: str) -> str:
		government = self.parts.cast.cast().government_of(holder)
		return country_rules.treasury_account(holder, self.needs.seat_list()["joined"], None if government is None else government.actor_id)

	def partner_catch_chance(self, civilization_id: str, share_of_holding: float) -> float:
		return country_rules.partner_catch_chance(self.parts.cast.seeded_actor_registry(), self.parts.cast.actor_world(), civilization_id, share_of_holding)

	def teaching_knowledge(self) -> Tuple[Dict[str, set], set, Any]:
		"""(nodes held by each active actor, what the society already knows, what has been demonstrated): who can teach a trade."""
		return (country_rules.knowledge_by_actor(self.parts.cast.cast().actors), set(self.needs.techniques_granted()),
		        self.parts.cast.actor_world().knowledge.demonstrated())

	def harvest_share_taken(self, material: str) -> float:
		"""Share of the harvest of a material the home state's forms take from growers; none without a government."""
		if self.parts.cast.cast().government_of(None) is None:
			return 0.0
		return tax_burden.harvest_share_taken(self.parts.cast.actor_world(), material)
