"""What a country's state enterprises (and any firm of the country) are booked at: the prices, wages and cost scale of the
country the plant stands in, read through its own part of the economy (Complaint 649)."""
from typing import Any, Optional

from .business_plant_books import PlantBooks, books_at_country_prices
from .no_country_economy import NoCountryEconomy


class CountryBooksView:
	"""The plant-books reading of `CountryWorld`; `profile`, `_shared` and `_own_economy` are its."""

	profile: Any
	_shared: Any

	def _own_economy(self) -> Any:
		raise NotImplementedError

	def plant_books(self, node_id: str, opened_year: int, rivals: float, size: float) -> Optional[PlantBooks]:
		"""Takings, upkeep and wages of a plant at `size` founding sizes at the country's own prices, wages and cost scale (the
		civilisation file's scale on the tree's book coin); None when its economy has no part for it, no wage for a trade
		the crew needs, or the concern sells into a goods category."""
		try:
			economy = self._own_economy()
		except NoCountryEconomy:
			return None
		shared = self._shared
		return books_at_country_prices(
			shared.book_takings(node_id, opened_year), shared.book_upkeep(node_id), shared.concern_staff(node_id), size,
			shared.span_factor(size), self.profile.price_index, shared.market_factor_at(node_id, economy.price_per_unit),
			economy.pay_per_person_year, shared.in_goods_category(node_id), rivals)
