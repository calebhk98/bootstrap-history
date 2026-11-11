"""Where a country's plants find their crew: the people of the trade in that country's own labour markets, less those
its other actors already employ (Complaint 649)."""
from typing import Any

from .country_part import SharedPart
from .research_pricing import cost_at_country_prices, hours_at_pay, materials_at_quotes
from .no_country_economy import NoCountryEconomy


def people_left(people_in_markets: float, held_by_others: float) -> float:
	"""People of a trade the markets hold that no other employer of the country has."""
	return max(0.0, people_in_markets - held_by_others)


class CountryResearch(SharedPart):
	"""The research reading of `CountryWorld`."""

	part = "research"
	# home: research cost and contact are properties of the technique and the shared map
	home_members = frozenset(("contact_volume", "material_tonnes", "purchasable_substitute_discount", "research_trades", "unsold_materials"))

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

	def research_cost(self, node_id: str, max_age_years: int) -> float:
		"""Money to pioneer the node in this country: its materials at the country's own quotes, its hours at the country's own
		pay, its capital at the country's price level. Refuses (NoCountryEconomy) where the country quotes a material nowhere
		or the economy has no part for it; never the founder's figure. Worked out each time (the home figure's cache is the
		founder's)."""
		world = self.world
		node = world.setting.nodes[node_id]
		cost = cost_at_country_prices(
			float(node.get("cap") or 0.0), world.profile.price_index,
			materials_at_quotes(self.shared.material_tonnes(node_id), world.quotes.material_cost),
			hours_at_pay(node.get("lab") or {}, world.labour.hourly_pay))
		if cost is None:
			raise NoCountryEconomy(world.profile.country, "price of a material of %s" % node_id)
		return cost
