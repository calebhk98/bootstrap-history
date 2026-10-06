"""The traders' route scan prices only pairs whose price gap can exceed freight, and finds the routes an
exhaustive scan over every (material, source, destination) triple finds."""

QUICK_TOPIC = True

import random

from .harness import check

from sim.agents.api import ActorRecord
from sim.agents.policy import Option
from sim.agents.trader import route_key, route_terms
from sim.agents.trader_entry import candidate_routes
from sim.agents.tuning import ENTREPRENEURIAL_CAPITAL_SHARE
from sim.agents.tuning_trader import TRADER_DEPTH_SHARE, TRADER_RISK_SHARE

from .test_agents_traders import TradeWorld, make_registry

MATERIALS = ("grain", "iron", "salt")


class CountingWorld(TradeWorld):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.freight_calls = 0

	def freight_between(self, source, destination, material, tonnes):
		self.freight_calls += 1
		return super().freight_between(source, destination, material, tonnes)


def build_world(prices, seed=0):
	rng = random.Random(seed)
	depth = {place: {material: rng.uniform(100.0, 900.0) for material in MATERIALS} for place in prices}
	world = CountingWorld(prices, depth, freight=2.0)
	world.output = 1.0e9
	return world


def random_world(place_count, seed):
	rng = random.Random(seed)
	prices = {"place%02d" % number: {material: rng.uniform(5.0, 25.0) for material in MATERIALS}
			  for number in range(place_count)}
	return build_world(prices, seed)


def exhaustive_candidates(world):
	"""Every triple priced, as the entry scan did before it pruned."""
	capital_limit = world.society_output() * ENTREPRENEURIAL_CAPITAL_SHARE
	rate = world.market_rate()
	found = []
	for material in sorted(world.trade_materials()):
		for source in sorted(world.trade_places(None)):
			for destination in sorted(world.trade_places(source)):
				terms = route_terms(world, source, destination, material) if source != destination else None
				if terms is None or terms["gain"] <= 0.0:
					continue
				tonnes = min(world.market_depth(material, destination) * TRADER_DEPTH_SHARE,
							 capital_limit / terms["outlay"])
				if tonnes <= 0.0:
					continue
				gain = tonnes * terms["gain"]
				if gain <= tonnes * terms["outlay"] * rate:
					continue
				found.append((gain, route_key(material, source, destination)))
	found.sort(key=lambda item: (-item[0], item[1]))
	return found


def exhaustive_options(trader, world):
	"""Every triple priced, as the trader's scan did before it pruned."""
	budget = trader.cargo_budget(world)
	rate = max(world.market_rate(), 0.0)
	options = []
	places = trader.places(world)
	planned = {}
	for material in sorted(world.trade_materials()):
		for source in places:
			for destination in places:
				terms = route_terms(world, source, destination, material) if source != destination else None
				if terms is None or terms["gain"] <= 0.0:
					continue
				arriving = planned.get((material, destination), 0.0)
				depth = world.market_depth(material, destination)
				room = max(0.0, depth * TRADER_DEPTH_SHARE - world.delivered_this_year(material, destination) - arriving)
				tonnes = min(room, budget / terms["outlay"])
				if tonnes <= 0.0:
					continue
				planned[(material, destination)] = arriving + tonnes
				options.append(Option(
					subject=route_key(material, source, destination),
					worth=tonnes * (terms["sold"] - terms["bought"] * rate - terms["bought"] * TRADER_RISK_SHARE),
					cost=tonnes * terms["outlay"],
					detail={"material": material, "source": source, "destination": destination, "tonnes": tonnes}))
	return options


def summary(options):
	return [(option.subject, option.worth, option.cost, option.detail) for option in options]


# ---- the same routes as the exhaustive scan ---------------------------------------------------
for seed in (1, 2, 3):
	world = random_world(7, seed)
	registry = make_registry()
	scanned = [(gain, key) for gain, key, _route in candidate_routes(registry, world)]
	check("entry scan finds what the exhaustive scan finds (seed %d)" % seed,
		  scanned == exhaustive_candidates(world) and len(scanned) > 0, len(scanned))

	trader = registry.add("trader:99", ActorRecord(kind="trader", location="place00", money=1.0e6, founded_year=100))
	options = trader.route_options(world)
	check("a trader's options are those of the exhaustive scan, in order (seed %d)" % seed,
		  summary(options) == summary(exhaustive_options(trader, world)) and len(options) > 0, len(options))

# ---- work no longer grows with places squared -------------------------------------------------
PLACE_COUNT = 30
flat = {"place%02d" % number: {material: 20.0 for material in MATERIALS} for number in range(PLACE_COUNT)}
flat["place00"] = {material: 10.0 for material in MATERIALS}  # one cheap place; no other pair has a gap
world = build_world(flat)
registry = make_registry()
trader = registry.add("trader:99", ActorRecord(kind="trader", location="place00", money=1.0e6, founded_year=100))
trader.route_options(world)
check("a trader prices freight only for pairs with a price gap",
	  world.freight_calls <= PLACE_COUNT * len(MATERIALS), world.freight_calls)
world.freight_calls = 0
candidate_routes(registry, world)
check("the entry scan prices freight only for pairs with a price gap",
	  world.freight_calls <= PLACE_COUNT * len(MATERIALS), world.freight_calls)
