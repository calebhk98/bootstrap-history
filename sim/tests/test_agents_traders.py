"""Traders: founded where a price gap pays, carry goods cheap to dear within capital and depth, and exit on losses."""

QUICK_TOPIC = True

from .harness import check

from sim.agents.api import ActorRecord, ActorRegistry, ActorsState
from sim.agents import registry as registry_module
from sim.agents.trader import Trader
from sim.agents.trader_entry import trader_entry
from sim.agents.tuning import EXIT_LOSS_YEARS
from sim.agents.tuning_trader import TRADER_DEPTH_SHARE, TRADER_FOUNDINGS_PER_YEAR

from .agents_fake_world import FakeWorld


class TradeWorld(FakeWorld):
	"""Places with prices and buying depth; carriage per tonne between any two; shipments tallied."""

	def __init__(self, prices, depth, freight=2.0, slippage=0.0, **kwargs):
		super().__init__(**kwargs)
		self.place_prices = prices  # place -> material -> price per tonne
		self.depth = depth  # place -> material -> tonnes a year
		self.freight_per_tonne = freight
		self.slippage = slippage  # share of the sale takings lost on the way
		self.shipped = {}
		self.countries = {}

	def trade_places(self, location):
		everywhere = sorted(self.place_prices)
		return everywhere if location is None else [place for place in everywhere if place != location]

	def trade_materials(self):
		return sorted({material for goods in self.place_prices.values() for material in goods})

	def price_at(self, material, place):
		return self.place_prices.get(place, {}).get(material, 0.0)

	def freight_between(self, source, destination, material, tonnes):
		return self.freight_per_tonne * tonnes

	def market_depth(self, material, place):
		return self.depth.get(place, {}).get(material, 0.0)

	def delivered_this_year(self, material, destination):
		return sum(tonnes for (good, _source, place), tonnes in self.shipped.items()
				   if good == material and place == destination)

	def ship(self, trader_id, material, tonnes, source, destination):
		key = (material, source, destination)
		self.shipped[key] = self.shipped.get(key, 0.0) + tonnes
		return (tonnes * self.price_at(material, source),
				tonnes * self.price_at(material, destination) * (1.0 - self.slippage))

	def country_of_place(self, place):
		return self.countries.get(place)

	def new_year(self):
		self.shipped = {}
		self.year += 1


def make_world(gap_price=20.0, freight=2.0, slippage=0.0, output=1.0e9):
	world = TradeWorld({"town": {"grain": 10.0}, "port": {"grain": gap_price}},
					   {"port": {"grain": 1000.0}, "town": {"grain": 1000.0}},
					   freight=freight, slippage=slippage)
	world.output = output
	return world


def make_registry():
	return ActorRegistry(ActorsState(home_country="home"))


def add_trader(registry, money, year=100):
	return registry.add("trader:99", ActorRecord(kind="trader", location="town", money=money, founded_year=year))


# ---- a gap above freight founds a trader, who ships cheap to dear -----------------------------
world = make_world()
registry = make_registry()
founded = trader_entry(registry, world)
check("a gap above freight and interest founds a trader", len(founded) == 1 and founded[0].startswith("trader:"), founded)
trader = registry.get(founded[0])
check("the trader is a Trader of kind trader at the route's source",
	  isinstance(trader, Trader) and trader.kind == "trader" and trader.record.location == "town")
check("opening capital is booked from the pooled edge", trader.record.income.get("edge:pooled capital", 0.0) > 0.0, trader.record.income)
opening = trader.money
trader.advance(world)
route = trader.record.routes.get("grain@town>port")
check("the trader ships cheap to dear", route is not None and route["tonnes"] > 0.0 and route["material"] == "grain", trader.record.routes)
check("no route runs from dear to cheap", not any(key.endswith("@port>town") for key in trader.record.routes))
check("the trade made a profit", trader.money > opening and trader.record.last_margin > 0.0)
check("route results are recorded", route["margin"] > 0.0 and route["years"] == 1, route)

# ---- a gap below freight plus interest: no entry, no shipping ---------------------------------
thin = make_world(gap_price=11.5)  # 1.5 gap against 2.0 freight
registry = make_registry()
check("a gap below freight founds no trader", trader_entry(registry, thin) == [])
idle = add_trader(registry, 1000.0)
idle.advance(thin)
check("an existing trader does not ship when the gap does not pay", not idle.record.routes and idle.money == 1000.0)
interest_gap = make_world(gap_price=12.5)  # clears freight, not freight plus a year's interest and risk at a high rate
interest_gap.rate = 0.5
registry = make_registry()
check("a gap eaten by interest founds no trader", trader_entry(registry, interest_gap) == [])

# ---- cargo bounded by capital and by the depth share ------------------------------------------
world = make_world()
registry = make_registry()
small = add_trader(registry, 120.0)  # twelve tonnes' outlay at ten plus two
small.advance(world)
shipped = world.shipped.get(("grain", "town", "port"), 0.0)
check("cargo is bounded by the trader's capital", abs(shipped - 120.0 / 12.0) < 1e-9, shipped)
world = make_world()
registry = make_registry()
rich = add_trader(registry, 1.0e9)
rich.advance(world)
shipped = world.shipped.get(("grain", "town", "port"), 0.0)
check("cargo is bounded by the share of the buyers' depth", abs(shipped - 1000.0 * TRADER_DEPTH_SHARE) < 1e-9, shipped)

# ---- two traders on one gap stay within the depth share together ------------------------------
world = make_world()
registry = make_registry()
first = registry.add("trader:1", ActorRecord(kind="trader", location="town", money=1.0e9, founded_year=100))
second = registry.add("trader:2", ActorRecord(kind="trader", location="town", money=1.0e9, founded_year=100))
registry.advance(world)
total = world.shipped.get(("grain", "town", "port"), 0.0)
check("traders chasing one gap together stay within the depth share", total <= 1000.0 * TRADER_DEPTH_SHARE + 1e-9 and total > 0.0, total)
check("the second trader finds the depth taken", second.record.routes.get("grain@town>port", {}).get("tonnes", 0.0) == 0.0)
world.new_year()
check("a trader already serving the depth stops a new entrant",
	  trader_entry(registry, world) == [] or first.record.routes["grain@town>port"]["tonnes"] == 0.0)
registry = make_registry()
registry.add("trader:1", ActorRecord(kind="trader", location="town", money=1.0e9, founded_year=100,
									 routes={"grain@town>port": {"material": "grain", "source": "town", "destination": "port",
														  "tonnes": 1000.0 * TRADER_DEPTH_SHARE, "margin": 1.0, "years": 1}}))
check("current traders serving the whole depth block entry", trader_entry(registry, make_world()) == [])

# ---- money: the purse moves by received less paid, carriage and interest, exactly ------------
world = make_world(slippage=0.1)
registry = make_registry()
borrower = add_trader(registry, -50.0)  # in debt: pays interest
borrower.record.last_margin = 500.0
borrower.record.founded_year = 90
before = borrower.money
owed = borrower.debt() * borrower.borrowing_rate(world)
borrower.advance(world)
detail = borrower.record.routes["grain@town>port"]
tonnes = detail["tonnes"]
paid, received = tonnes * 10.0, tonnes * 20.0 * 0.9
expected = received - paid - world.freight_per_tonne * tonnes - owed
check("the purse changes by received less paid, freight and interest", abs(borrower.money - before - expected) < 1e-9,
	  (borrower.money - before, expected))
check("income and outlays by purpose keep the purse exact",
	  abs(borrower.money - (-50.0 + sum(borrower.record.income.values()) - sum(borrower.record.outlays.values()))) < 1e-9)
check("market, freight and interest are labelled",
	  {"edge:market purchase", "edge:freight", "interest"} <= set(borrower.record.outlays)
	  and "edge:market sale" in borrower.record.income, (borrower.record.outlays, borrower.record.income))
check("a trader in debt still ships on the credit it may borrow", tonnes * 12.0 > 0.0 and not borrower.borrows_for_copies)

# ---- losses for EXIT_LOSS_YEARS make it exit; it keeps its money record ----------------------
world = make_world(slippage=0.9)  # the sale takes far less than the price promised
registry = make_registry()
loser = add_trader(registry, 1000.0)
years = 0
while loser.record.exited_year is None and years < EXIT_LOSS_YEARS + 3:
	world.new_year()
	loser.advance(world)
	years += 1
check("sustained losses make a trader exit after the declared years", loser.record.exited_year is not None and years == EXIT_LOSS_YEARS, years)
kept = loser.money
check("an exited trader keeps its money record",
	  abs(loser.money - (1000.0 + sum(loser.record.income.values()) - sum(loser.record.outlays.values()))) < 1e-9)
world.new_year()
loser.advance(world)
check("an exited trader stops acting", loser.money == kept)

# ---- determinism and bounded founding ----------------------------------------------------------
def run_two_years(places):
	prices = {name: {"grain": 10.0 + 10.0 * index, "salt": 50.0 - 5.0 * index} for index, name in enumerate(places)}
	depth = {name: {"grain": 1000.0, "salt": 1000.0} for name in places}
	run_world = TradeWorld(prices, depth)
	run_world.output = 1.0e9
	run_registry = make_registry()
	counts = []
	for _year in range(2):
		registry_module_run = trader_entry(run_registry, run_world)
		counts.append(len(registry_module_run))
		run_registry.advance(run_world)
		run_world.new_year()
	return counts, {key: (record.money, sorted(record.routes)) for key, record in sorted(run_registry.state.records.items())}


first_run = run_two_years(["a", "b", "c", "d"])
check("a run is deterministic", first_run == run_two_years(["a", "b", "c", "d"]))
check("founding a year is bounded however many routes pay", max(first_run[0]) <= TRADER_FOUNDINGS_PER_YEAR, first_run[0])
check("ids are unique", len(first_run[1]) == len(set(first_run[1])))

# ---- country of the source place, when the world tells it --------------------------------------
world = make_world()
world.countries = {"town": "far"}
registry = make_registry()
trader_id = trader_entry(registry, world)[0]
check("the trader's country is the source place's country", registry.get(trader_id).record.country == "far")
check("trader_entry is a registered spawner", "trader_entry" in [name for name, _spawner in registry_module.SPAWNERS])

# ---- review regressions: room is per destination, idle traders leave, exited actors rest -------
three = make_world()
three.place_prices["farm"] = {"grain": 10.0}
three.depth["farm"] = {}
registry = make_registry()
both_sources = registry.add("trader:9", ActorRecord(kind="trader", location="town", money=1.0e9, founded_year=100))
three.trade_places = lambda location: ["farm", "port", "town"]
both_sources.advance(three)
into_port = sum(tonnes for (good, _source, place), tonnes in three.shipped.items() if good == "grain" and place == "port")
check("cargo from two sources into one market stays within its depth share",
	  0.0 < into_port <= 1000.0 * TRADER_DEPTH_SHARE + 1e-9, into_port)

idle_world = make_world(gap_price=10.0)
registry = make_registry()
idle = registry.add("trader:7", ActorRecord(kind="trader", location="town", money=500.0, founded_year=100))
for _year in range(EXIT_LOSS_YEARS):
	registry.advance(idle_world)
	idle_world.new_year()
check("a trader with nothing worth carrying for long enough gives up", idle.record.exited_year is not None)
check("a trader that gives up hands what it holds back to its owners", idle.money == 0.0
	  and idle.record.outlays.get("edge:pooled capital") == 500.0, (idle.money, idle.record.outlays))
