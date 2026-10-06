"""Which (source, destination) pairs of a material can gain: the terms of a route, and a scan that prices carriage only
where the price gap can exceed it."""
from bisect import bisect_right
from typing import Any, Callable, Dict, Iterator, List, Optional, Sequence, Tuple

from .tuning_trader import TRADER_RISK_SHARE

# a pair at the edge of paying is priced in full, so float rounding never drops a route that gains
GAP_SLACK = 1e-9
PAYING_SEARCH_STEPS = 24


def route_key(material: str, source: str, destination: str) -> str:
	return "%s@%s>%s" % (material, source, destination)


def route_terms(world: Any, source: str, destination: str, material: str) -> Optional[Dict[str, float]]:
	"""Per tonne: what a cargo costs to buy and carry, and what carrying it gains before the cost of
	its capital. None when either end has no price."""
	bought = world.price_at(material, source)
	sold = world.price_at(material, destination)
	if not bought or not sold or bought <= 0.0 or sold <= 0.0:
		return None
	freight = world.freight_between(source, destination, material, 1.0)
	outlay = bought + freight
	return {"bought": bought, "sold": sold, "freight": freight, "outlay": outlay,
			"gain": sold - outlay - bought * TRADER_RISK_SHARE}


def price_answers(world: Any, material: str, destination: str) -> bool:
	"""Whether the destination's market moves with cargo, so the price limits a cargo and not a share of depth."""
	return world.price_after_cargo(material, destination, 0.0, True) is not None


def paying_tonnes(world: Any, source: str, destination: str, material: str, terms: Dict[str, float],
				  tonnes: float, rate: float) -> float:
	"""The most of `tonnes` that still pays once the cargo has moved the prices it meets: the destination's price
	after the cargo lands, less carriage, risk and the interest on what it cost, must exceed the source's price
	after the cargo is taken. A place whose market does not answer keeps its price. Prices move monotonically
	with cargo, so the limit is found by halving."""
	def pays(cargo: float) -> bool:
		sold = world.price_after_cargo(material, destination, cargo, True)
		bought = world.price_after_cargo(material, source, cargo, False)
		sold = terms["sold"] if sold is None else sold
		bought = terms["bought"] if bought is None else bought
		return sold - bought * (1.0 + TRADER_RISK_SHARE + rate) - terms["freight"] > 0.0
	if tonnes <= 0.0 or pays(tonnes):
		return max(tonnes, 0.0)
	low, high = 0.0, tonnes
	for _step in range(PAYING_SEARCH_STEPS):
		middle = (low + high) / 2.0
		low, high = (middle, high) if pays(middle) else (low, middle)
	return low


def gaining_routes(world: Any, material: str, sources: Sequence[str],
				   destinations_of: Callable[[str], Sequence[str]]) -> Iterator[Tuple[str, str, Dict[str, float]]]:
	"""(source, destination, terms) for every pair of this material that gains, in source then destination order.
	A pair gains only if the destination's price exceeds the source's by at least the share lost on the way, so
	destinations are found by a sorted search on price and carriage is priced for those alone."""
	price_of: Dict[str, float] = {}
	ladders: Dict[Tuple[str, ...], List[Tuple[float, int, str]]] = {}
	for source in sources:
		destinations = tuple(destinations_of(source))
		ladders.setdefault(destinations, [])
		for place in (source,) + destinations:
			if place not in price_of:
				price = world.price_at(material, place)
				price_of[place] = price if price and price > 0.0 else 0.0
	for destinations, ladder in ladders.items():
		ladder.extend(sorted((price_of[place], order, place) for order, place in enumerate(destinations)
							 if price_of[place] > 0.0))
	for source in sources:
		bought = price_of[source]
		if bought <= 0.0:
			continue
		ladder = ladders[tuple(destinations_of(source))]
		floor = bought * (1.0 + TRADER_RISK_SHARE) * (1.0 - GAP_SLACK)
		start = bisect_right(ladder, floor, key=lambda entry: entry[0])
		for _price, _order, destination in sorted(ladder[start:], key=lambda entry: entry[1]):
			if destination == source:
				continue
			terms = route_terms(world, source, destination, material)
			if terms is not None and terms["gain"] > 0.0:
				yield source, destination, terms
