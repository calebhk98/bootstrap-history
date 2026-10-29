"""The cast's answers about countries, treasuries and the people of the home country, mixed into `Actors`."""
from typing import Any, Dict, FrozenSet, List, Optional, Tuple

from sim.agents.api import tax_burden

from . import country_rules


class CountryViews:
	"""Mixed into `Actors`. Needs: civilisation, seat_list."""

	needs: Any

	def has_state(self, owner: str) -> bool:
		return country_rules.is_country_with_state(owner, str(self.needs.civilisation()["id"]), self.cast().state.countries)  # type: ignore[attr-defined]

	def countries(self) -> List[str]:
		return list(self.cast().state.countries)  # type: ignore[attr-defined]

	def organised_factions(self, owner: str) -> List[Tuple[float, float]]:
		return country_rules.organised_factions(self.cast().of_kind("interest_group"), str(self.needs.civilisation()["id"]), owner)  # type: ignore[attr-defined]

	def home_country(self) -> Dict[str, Any]:
		state = self.cast().state  # type: ignore[attr-defined]
		return country_rules.home_country_facts(state.home_country, state.countries)

	def state_knowledge(self) -> FrozenSet[str]:
		"""The nodes the home government holds."""
		return frozenset(self.state_treasury().knowledge)  # type: ignore[attr-defined]

	def holder_treasury(self, holder: str) -> str:
		government = self.cast().government_of(holder)  # type: ignore[attr-defined]
		return country_rules.treasury_account(holder, self.needs.seat_list()["joined"], None if government is None else government.actor_id)

	def partner_catch_chance(self, civilization_id: str, share_of_holding: float) -> float:
		return country_rules.partner_catch_chance(self.seeded_actor_registry(), self.actor_world(), civilization_id, share_of_holding)  # type: ignore[attr-defined]

	def teaching_knowledge(self) -> Tuple[Dict[str, set], set, Any]:
		"""(nodes held by each active actor, what the society already knows, what has been demonstrated): who can teach a trade."""
		return (country_rules.knowledge_by_actor(self.cast().actors), set(self.needs.techniques_granted()),  # type: ignore[attr-defined]
		        self.actor_world().demonstrated())  # type: ignore[attr-defined]

	def harvest_share_taken(self, material: str) -> float:
		"""Share of the harvest of a material the home state's forms take from growers; none without a government."""
		if self.cast().government_of(None) is None:  # type: ignore[attr-defined]
			return 0.0
		return tax_burden.harvest_share_taken(self.actor_world(), material)  # type: ignore[attr-defined]
