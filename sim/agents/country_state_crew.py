"""Where a country's plants find their crew: the people of the trade in that country's own labour markets, less those
its other actors already employ (Complaint 649)."""
from typing import Any, Optional

from .no_country_economy import NoCountryEconomy


def people_left(people_in_markets: float, held_by_others: float) -> float:
	"""People of a trade the markets hold that no other employer of the country has."""
	return max(0.0, people_in_markets - held_by_others)


class CountryCrewView:
	"""The crew reading of `CountryWorld`; `profile`, `_holder` and `_own_economy` are its."""

	profile: Any
	_holder: Any
	_shared: Any

	def _own_economy(self) -> Any:
		raise NotImplementedError

	def research_hands(self, actor: Any, family: str) -> float:
		"""People of a trade family the actor can put on research: its staff and the people its own country's labour markets
		hold in those trades that no other employer there has. Refuses (NoCountryEconomy) where the economy has no part for
		the country; never the founder's pool."""
		hands = 0.0
		for trade in self._shared.research_trades(family):
			left = self.free_fte(trade, actor.identity())
			if left is None:
				raise NoCountryEconomy(self.profile.country, "research hands")
			hands += actor.workforce.get(trade, 0.0) + left
		return hands

	def free_fte(self, trade: str, actor_id: Optional[str]) -> Optional[float]:
		"""People of a trade left in this country's labour markets for `actor_id`; None when the economy has no part for the
		country or the holder cannot count its employers, never the founder's pool."""
		try:
			economy = self._own_economy()
		except NoCountryEconomy:
			return None
		count = getattr(self._holder, "staff_fte_in_country", None)
		if not callable(count):
			return None
		return people_left(economy.people_of_trade(trade), count(trade, self.profile.country, actor_id))
