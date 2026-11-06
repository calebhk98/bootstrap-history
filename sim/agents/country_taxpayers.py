"""What a country's state sees of its taxpayers: the firms and seats it can see, its reach and the levy it assesses."""
from typing import Any, List, Optional, Tuple

from . import taxpayer_income
from .country_part import SharedPart


class CountryTaxpayers(SharedPart):
	"""The country's taxpayers, its capacity and its tax share."""

	part = "taxpayers"
	# home: who is taxable and how visible their scale is are the shared world's
	home_members = frozenset(("seat_taxpayers", "visible_scale_of"))

	def state_reach(self) -> float:
		"""What the country's paid officials collect of what is due, over its roads (collection_world.py)."""
		return self.world.collection.collectible_share()

	def tax_share(self) -> float:
		"""Share of its taxpayers' income the country's state starts out taking."""
		return self.world.profile.tax_share

	def visible_taxpayers(self) -> List[Tuple[float, float]]:
		"""(visible scale, taxable income) of the firms and the players' seats of the country the state can see."""
		holder = self.world.holder
		firms = holder.concerns.active_firms()
		country = self.world.profile.country
		seats = list(self.shared.seat_taxpayers(country))
		return seats + [(self.shared.visible_scale_of(firm), income) for firm, income in taxpayer_income.firm_incomes_in(
			firms, country, holder.countries.country_of, holder.countries.country_of_tile)]

	def notice_over(self, scale: float, capacity: Optional[float] = None) -> float:
		return self.shared.notice_over(scale, self.state_reach() if capacity is None else capacity)

	def levy_shares(self, scale: float, protection: float = 0.0, state: Any = None) -> Any:
		"""(requisition, office) shares of income this country's state assesses at a visible scale: its own capacity,
		tax share and the rates its shortfall set last year."""
		requisition, office = self.world.setting.government().levy_rates()
		return self.shared.levy_shares(scale, protection, (self.state_reach(), self.tax_share(), requisition, office))
