"""What a country's state enterprises (and any firm of the country) are booked at: the prices, wages and cost scale of the
country the plant stands in, read through its own part of the economy (Complaint 649)."""
from typing import Optional

from .business_plant_books import PlantBooks, books_at_country_prices
from .country_army import output_factor
from .country_part import SharedPart


class CountryEnterprises(SharedPart):
	"""The plant-books reading of `CountryWorld`."""

	part = "enterprises"
	# home: books of a technique's takings and inputs are read at the shared world's prices
	home_members = frozenset(("book_takings", "book_takings_at_full_ramp", "book_upkeep", "concern_inputs", "concerns_making", "in_goods_category", "market_factor_at", "materials_made_by"))

	def plant_books(self, node_id: str, opened_year: int, rivals: float, size: float) -> Optional[PlantBooks]:
		"""Takings, upkeep and wages of a plant at `size` founding sizes at the country's own prices, wages and cost scale (the
		civilisation file's scale on the tree's book coin); None when its economy has no part for it, no wage for a trade
		the crew needs, or the concern sells into a goods category."""
		economy = self.world.own.get_or_none()
		if economy is None:
			return None
		shared = self.shared
		world = self.world
		return books_at_country_prices(
			shared.book_takings(node_id, opened_year), shared.book_upkeep(node_id), world.concerns.concern_staff(node_id), size,
			world.capacity.span_factor(size), world.profile.price_index, shared.market_factor_at(node_id, economy.price_per_unit),
			economy.pay_per_person_year, shared.in_goods_category(node_id), rivals, output_factor(world))
