"""What running a concern costs and takes in the country the actor stands in: the site's rent, the manager's pay, the
takings of a ramped-up concern and the yearly costs an entrant weighs, from that country's own part of the economy
(Complaint 649). A figure the country keeps no record of is None, never the home figure."""
from typing import Any, Callable, Mapping, Optional, Tuple

from .business_plant_books import wage_bill_at
from .no_country_economy import NoCountryEconomy


def rent_of_site(hectares: float, rent_per_hectare: Optional[float]) -> Optional[float]:
	"""Yearly rent of a site of `hectares`; None when the country let no land to take a rent from."""
	return None if rent_per_hectare is None else hectares * rent_per_hectare


def gross_at_country_prices(book_takings_at_full_ramp: float, cost_scale: float, market_factor: float,
							shares_goods_market: bool, output_factor: float) -> Optional[float]:
	"""Yearly takings of a ramped-up concern at the country's cost scale and market factor, less what its own hazards and
	wars take (`output_factor`); None for a concern in a goods category, whose demand is the home households'."""
	if shares_goods_market:
		return None
	return book_takings_at_full_ramp * cost_scale * market_factor * output_factor


def costs_at_country_prices(book_upkeep: float, staff: Mapping[str, float], cost_scale: float, span_factor: float,
							pay_per_person_year: Callable[[str], Optional[float]]) -> Optional[Tuple[float, float]]:
	"""(upkeep, wage bill) of a plant at its founding size in the country; None when a trade of the crew has no pay there."""
	wages = wage_bill_at(staff, 1.0, span_factor, pay_per_person_year)
	if wages is None:
		return None
	return book_upkeep * cost_scale, wages


class CountrySiteView:
	"""The site, pay and entry-figure readings of `CountryWorld`; `profile`, `_shared` and `_own_economy` are its."""

	profile: Any
	_shared: Any

	def output_factor(self) -> float:
		raise NotImplementedError

	def _own_economy(self) -> Any:
		raise NotImplementedError

	def _economy_or_none(self) -> Optional[Any]:
		try:
			return self._own_economy()
		except NoCountryEconomy:
			return None

	def site_rent(self, node_id: str, capacity: float = 1.0, tile: Optional[str] = None) -> Optional[float]:
		"""Yearly rent of the site a concern at `capacity` founding sizes occupies, at the rent the country's land market let
		land at (on `tile` when it is the country's); None when the economy has no part for the country or let no land there."""
		economy = self._economy_or_none()
		if economy is None:
			return None
		return rent_of_site(self._shared.site_hectares(node_id, capacity), economy.land_rent_at(tile))

	def hourly_pay(self, trade: str) -> Optional[float]:
		"""What an hour of a trade pays in the country's labour markets; None when they pay nothing for it."""
		economy = self._economy_or_none()
		pay = None if economy is None else economy.pay_per_person_year(trade)
		return None if pay is None else pay / self._shared.hours_per_person_year

	def concern_gross(self, node_id: str) -> Optional[float]:
		"""Yearly takings of a concern once ramped up, at the country's prices; None when the economy has no part for the
		country or the concern sells into a goods category."""
		economy = self._economy_or_none()
		if economy is None:
			return None
		shared = self._shared
		return gross_at_country_prices(shared.book_takings_at_full_ramp(node_id), self.profile.price_index,
									   shared.market_factor_at(node_id, economy.price_per_unit), shared.in_goods_category(node_id),
									   self.output_factor())

	def plant_costs(self, node_id: str) -> Optional[Tuple[float, float]]:
		"""(upkeep, wage bill) of a plant at its founding size in the country; None when it cannot be read."""
		economy = self._economy_or_none()
		if economy is None:
			return None
		shared = self._shared
		return costs_at_country_prices(shared.book_upkeep(node_id), shared.concern_staff(node_id), self.profile.price_index,
									   shared.span_factor(1.0), economy.pay_per_person_year)
