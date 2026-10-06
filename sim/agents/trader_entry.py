"""Founding traders: a route whose price gap pays more than the capital a cargo ties up would earn."""
from typing import Any, Dict, List, Tuple

from .records import ActorRecord
from .trader_routes import gaining_routes, paying_tonnes, price_answers, route_key
from .tuning import ENTREPRENEURIAL_CAPITAL_SHARE
from .tuning_trader import TRADER_DEPTH_SHARE, TRADER_FOUNDINGS_PER_YEAR


def served_tonnes(registry: Any) -> Dict[Tuple[str, str], float]:
	"""(material, destination) -> tonnes the active traders brought there last year, from any source."""
	served: Dict[Tuple[str, str], float] = {}
	for trader in registry.of_kind("trader"):
		if trader.record.exited_year is not None:
			continue
		for route in trader.record.routes.values():
			market = (route["material"], route.get("destination", ""))
			served[market] = served.get(market, 0.0) + route["tonnes"]
	return served


def candidate_routes(registry: Any, world: Any) -> List[Tuple[float, str, Dict[str, Any]]]:
	"""(yearly gain, key, route) for each route that pays an entrant, best first. The cargo is what
	the pooled capital buys, within the buyers' depth no trader already serves."""
	capital_limit = world.society_output() * ENTREPRENEURIAL_CAPITAL_SHARE
	capital_rate = world.market_rate()
	served = served_tonnes(registry)
	found = []
	for material in sorted(world.trade_materials()):
		sources = sorted(world.trade_places(None))
		for source, destination, terms in gaining_routes(
				world, material, sources, lambda place: sorted(world.trade_places(place))):
			key = route_key(material, source, destination)
			tonnes = capital_limit / terms["outlay"]
			if price_answers(world, material, destination):
				tonnes = paying_tonnes(world, source, destination, material, terms, tonnes, capital_rate)
			else:
				unserved = world.market_depth(material, destination) * TRADER_DEPTH_SHARE - served.get((material, destination), 0.0)
				tonnes = min(unserved, tonnes)
			if tonnes <= 0.0:
				continue
			gain = tonnes * terms["gain"]
			if gain <= tonnes * terms["outlay"] * capital_rate:
				continue
			found.append((gain, key, {"material": material, "source": source, "destination": destination,
									  "tonnes": tonnes, "capital": tonnes * terms["outlay"]}))
	found.sort(key=lambda item: (-item[0], item[1]))
	return found


def trader_entry(registry: Any, world: Any) -> List[str]:
	"""Found a trader on each of the best routes that pay, a bounded number a year, and not on a
	route whose buyers current traders already supply to the declared share."""
	registry.world = world
	founded: List[str] = []
	taken = set()
	for gain, key, route in candidate_routes(registry, world):
		if len(founded) >= TRADER_FOUNDINGS_PER_YEAR:
			break
		pair = (route["material"], route["destination"])
		if pair in taken:
			continue  # one entrant a year per market, so the depth is not counted twice
		taken.add(pair)
		number = len(registry.state.records) + 1
		while "trader:%d" % number in registry.state.records:
			number += 1
		trader_id = "trader:%d" % number
		country_of_place = getattr(world, "country_of_place", None)
		trader = registry.add(trader_id, ActorRecord(
			kind="trader", name=trader_id, location=route["source"], founded_year=world.year,
			country=country_of_place(route["source"]) if country_of_place else None))
		trader.credit(route["capital"], "edge:pooled capital")
		founded.append(trader_id)
	return founded


from .registry import register_spawner  # noqa: E402

register_spawner("trader_entry", trader_entry)
