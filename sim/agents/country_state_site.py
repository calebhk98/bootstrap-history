"""What running a concern costs and takes in the country the actor stands in: the site's rent, the manager's pay, the
takings of a ramped-up concern and the yearly costs an entrant weighs, from that country's own part of the economy
(Complaint 649). A figure the country keeps no record of is None, never the home figure."""
from typing import Callable, Mapping, Optional, Tuple

from .business_plant_books import wage_bill_at
from .country_army import output_factor
from .country_part import SharedPart


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
							pay_per_person_year: Callable[[str], float]) -> Tuple[float, float]:
	"""(upkeep, wage bill) of a plant at its founding size in the country."""
	return book_upkeep * cost_scale, wage_bill_at(staff, 1.0, span_factor, pay_per_person_year)


class CountrySite(SharedPart):
	"""The site reading of `CountryWorld`."""

	part = "site"
	# home: a site's hectares are a property of the site
	home_members = frozenset(("site_hectares",))

	def site_rent(self, node_id: str, capacity: float = 1.0, tile: Optional[str] = None) -> Optional[float]:
		"""Yearly rent of the site a concern at `capacity` founding sizes occupies, at the rent the country's land market let
		land at (on `tile` when it is the country's); None when the economy has no part for the country or let no land there."""
		economy = self.world.own.get_or_none()
		if economy is None:
			return None
		return rent_of_site(self.shared.site_hectares(node_id, capacity), economy.land_rent_at(tile))


class CountryConcerns(SharedPart):
	"""The entry-figure readings of `CountryWorld`."""

	part = "concerns"
	# home: a concern's margin, staff and costs are figures of the technique at the shared prices
	home_members = frozenset(("concern_margin", "concern_output_tonnes", "concern_staff", "concern_takings", "concern_wage_bill", "copy_cost", "copy_risk", "entry_gross", "proven_concerns", "ramp", "scale_ceiling", "upkeep"))

	def concern_gross(self, node_id: str) -> Optional[float]:
		"""Yearly takings of a concern once ramped up, at the country's prices; None when the economy has no part for the
		country or the concern sells into a goods category."""
		economy = self.world.own.get_or_none()
		if economy is None:
			return None
		enterprises = self.world.shared.enterprises
		return gross_at_country_prices(enterprises.book_takings_at_full_ramp(node_id), self.world.profile.price_index,
									   enterprises.market_factor_at(node_id, economy.price_per_unit), enterprises.in_goods_category(node_id),
									   output_factor(self.world))

	def plant_costs(self, node_id: str) -> Optional[Tuple[float, float]]:
		"""(upkeep, wage bill) of a plant at its founding size in the country; None when it cannot be read."""
		economy = self.world.own.get_or_none()
		if economy is None:
			return None
		shared = self.world.shared
		return costs_at_country_prices(shared.enterprises.book_upkeep(node_id), self.shared.concern_staff(node_id), self.world.profile.price_index,
									   shared.capacity.span_factor(1.0), economy.pay_per_person_year)
