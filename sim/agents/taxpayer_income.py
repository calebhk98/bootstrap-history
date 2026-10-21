"""Which country's state a firm's income is taxable in: the country each of its plants earns in.

A firm answers to one country (`ActorRecord.country`), but a plant stands on a tile and a tile belongs to a country. A firm's
yearly income is split among the countries of its operating plants by what each plant took; a plant with no tile, or on a
tile no country holds, earns in the firm's own country."""
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from .business_plant import OPERATING


def income_by_country(income: float, plants: Sequence[Tuple[Optional[str], float]], own_country: str,
					  country_of_tile: Callable[[str], Optional[str]]) -> Dict[str, float]:
	"""`income` shared among the countries of `plants` ((tile, takings) each) in proportion to what the plants took (equally
	while none took anything); the whole of it in `own_country` when there are no plants."""
	if not plants:
		return {own_country: income}
	weights = [max(0.0, takings) for _tile, takings in plants]
	total = sum(weights)
	if total <= 0.0:
		weights, total = [1.0] * len(plants), float(len(plants))
	shares: Dict[str, float] = {}
	for (tile, _takings), weight in zip(plants, weights):
		country = (country_of_tile(tile) if tile is not None else None) or own_country
		shares[country] = shares.get(country, 0.0) + income * weight / total
	return shares


def firm_incomes_in(firms: Sequence[Any], country: str, country_of: Callable[[Any], str],
					country_of_tile: Callable[[str], Optional[str]]) -> List[Tuple[Any, float]]:
	"""(firm, taxable income) of the firms with a plant earning in `country`; the income is the part earned there."""
	rows = []
	for firm in firms:
		plants = [(plant.tile, plant.takings) for plant in firm.record.business.plants if plant.state == OPERATING]
		split = income_by_country(max(0.0, firm.record.last_margin), plants, country_of(firm), country_of_tile)
		if country in split:
			rows.append((firm, split[country]))
	return rows


def tile_owners(profiles: Dict[str, Any]) -> Dict[str, str]:
	"""Each tile the countries' profiles hold, with the country that holds it (the lowest country id where two list it)."""
	owners: Dict[str, str] = {}
	for country in sorted(profiles, reverse=True):
		for tile in profiles[country].home_tiles:
			owners[tile] = country
	return owners
