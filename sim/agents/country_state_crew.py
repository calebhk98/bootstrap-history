"""Where a country's plants find their crew: the people of the trade in that country's own labour markets, less those
its other actors already employ (Complaint 649)."""
from typing import Any

from .country_part import SharedPart
from .no_country_economy import NoCountryEconomy


def people_left(people_in_markets: float, held_by_others: float) -> float:
	"""People of a trade the markets hold that no other employer of the country has."""
	return max(0.0, people_in_markets - held_by_others)


class CountryResearch(SharedPart):
	"""The research reading of `CountryWorld`."""

	part = "research"

	def research_hands(self, actor: Any, family: str) -> float:
		"""People of a trade family the actor can put on research: its staff and the people its own country's labour markets
		hold in those trades that no other employer there has. Refuses (NoCountryEconomy) where the economy has no part for
		the country; never the founder's pool."""
		hands = 0.0
		for trade in self.shared.research_trades(family):
			left = self.world.labour.free_fte(trade, actor.identity())
			if left is None:
				raise NoCountryEconomy(self.world.profile.country, "research hands")
			hands += actor.workforce.get(trade, 0.0) + left
		return hands
