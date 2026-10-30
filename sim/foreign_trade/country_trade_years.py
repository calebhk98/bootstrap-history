"""What crossed each country's border over the economy's external edge (trade with partners off the map), by year.

The country counterpart of `state.economy.foreign_trade_by_year`: {country: {year: {"in": money, "out": money}}} in coin, kept
for the last few years only. The goods the merchants carried between countries are kept apart (sim/economy/carried_book.py)."""
from typing import Dict

YEARS_KEPT = 3
IN, OUT = "in", "out"

CountryTrade = Dict[str, Dict[str, Dict[str, float]]]


def note(book: CountryTrade, country: str, year: int, imports: float, exports: float) -> None:
	"""Add a year's off-map imports and exports to a country's book; years older than the last few are dropped."""
	years = book.setdefault(country, {})
	entry = years.setdefault(str(year), {IN: 0.0, OUT: 0.0})
	entry[IN] += imports
	entry[OUT] += exports
	for old in [key for key in years if int(key) <= year - YEARS_KEPT]:
		del years[old]


def value(book: CountryTrade, country: str, year: int, direction: str) -> float:
	"""Money's worth the country imported ("in") or exported ("out") over the external edge in `year`; nothing crossed when
	the book has no entry for it."""
	return float(book.get(country, {}).get(str(year), {}).get(direction, 0.0))
