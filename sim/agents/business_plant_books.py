"""The three figures a plant's year is booked from (takings, upkeep, wages) as the economy the plant stands in states them.

At home they are the founder's engine's (`home_books`). For a plant in another country they are read from that
country's own part of the economy (`books_at_country_prices`): its prices value the goods, its labour markets pay the
crew, its cost scale carries the tree's book-coin money. A figure the country has no record of makes the whole
reading None, never the home figure; the plant then stands idle that year.
"""
from typing import Any, Callable, Mapping, NamedTuple, Optional, Tuple


class PlantBooks(NamedTuple):
	"""Yearly money of one plant at its size: takings before the crew found, upkeep without the crew's pay, the full wage bill."""
	takings: float
	upkeep: float
	wages: float


def home_books(world: Any, entry_key: str, opened_year: int, rivals: float, size: float) -> PlantBooks:
	"""The books of a plant in the home economy."""
	return PlantBooks(world.concerns.concern_takings(entry_key, opened_year, rivals, size), world.concerns.upkeep(entry_key, size),
					  world.concerns.concern_wage_bill(entry_key, size))


def home_costs(world: Any, entry_key: str) -> Tuple[float, float]:
	"""(upkeep, wage bill) of a plant of the concern at its founding size in the home economy."""
	return world.concerns.upkeep(entry_key), world.concerns.concern_wage_bill(entry_key)


def wage_bill_at(staff: Mapping[str, float], size: float, span_factor: float,
				 pay_per_person_year: Callable[[str], float]) -> float:
	"""Yearly wages of a plant run at `size` founding sizes, each trade's people paid what a person-year of it pays in the
	country (`span_factor` is the management-span lift of that size)."""
	return span_factor * sum(people * pay_per_person_year(trade) for trade, people in sorted(staff.items()))


def books_at_country_prices(book_takings: float, book_upkeep: float, staff: Mapping[str, float], size: float,
							span_factor: float, cost_scale: float, market_factor: float,
							pay_per_person_year: Callable[[str], float], shares_goods_market: bool,
							rivals: float, output_factor: float) -> Optional[PlantBooks]:
	"""A plant's books at a country's own figures. `book_takings` and `book_upkeep` are the tree's figures for one founding
	size in book coin (before any cost scale); `market_factor` is the country's market over long-run prices for what the
	plant sells and buys (the world's `market_factor_at` with the country's unit prices); `output_factor` is the share of its
	output the country's own hazards and wars leave (country_hazards.py).

	Takings are the book figure at the country's cost scale and market factor, shared among the operators of a concern with
	no market model. A concern in a goods category shares the home society's demand, which has no country record: None."""
	if shares_goods_market:
		return None
	wages = wage_bill_at(staff, size, span_factor, pay_per_person_year)
	takings = book_takings * cost_scale * size * market_factor * output_factor / (size + rivals)
	return PlantBooks(takings, book_upkeep * cost_scale * size, wages)
