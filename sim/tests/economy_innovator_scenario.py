"""A coffee-style market for scenario tests: several incumbent makers on a dear technique serve the
households' demand; in a later year a far cheaper technique for the same good becomes known and its
maker's capacity grows year by year. The test states every figure; nothing is read from data/."""
import dataclasses
from typing import Dict, List

from sim.economy import goods_market, market_curves
from sim.economy.economy import Economy
from sim.economy.households_basket import Basket, NeedSpec
from sim.economy.market_memory import market_key
from sim.economy.producers import Producer
from sim.economy.types import EDGE_MINT, GoodSpec, Recipe, Transfer
from sim.tests import economy_fixture as fixture
from sim.world.need_demand import NEED_SUBSTITUTION_ELASTICITY

COFFEE = "coffee_kg"
DEAR = Recipe("grow_coffee_dear", {COFFEE: 100.0}, {fixture.GRAIN: 1000.0}, {fixture.LABOURER: 1.0})
CHEAP = Recipe("grow_coffee_cheap", {COFFEE: 100.0}, {fixture.GRAIN: 10.0}, {fixture.LABOURER: 1.0})
ENTRANT = "producer:cheap_coffee"
ENTRY_YEAR = 3
YEARS = 24
START_CAPACITY_RUNS = 2.0
CAPACITY_GROWTH_PER_YEAR = 1.6          # the entrant's build-out is the scenario's input, not a decision


def coffee_setup():
    base = fixture.small_setup()
    specs = dict(base.specs)
    specs[COFFEE] = GoodSpec(COFFEE, 1.0, 0.1, 0.0, "drink")
    needs = base.basket.needs + (NeedSpec("coffee", 0.0, 0.3, ((COFFEE, 1.0),)),)
    need_data = dict(base.basket.need_data)
    need_data["coffee"] = {"surplus_budget_share": 0.3}
    recipes = dict(base.recipes)
    recipes[DEAR.recipe_id] = DEAR
    prices = dict(base.opening_prices)
    prices[COFFEE] = 3.5
    return dataclasses.replace(base, specs=specs, recipes=recipes, opening_prices=prices,
                               basket=Basket(needs, NEED_SUBSTITUTION_ELASTICITY, need_data))


def port_key(economy: Economy) -> str:
    return market_key(COFFEE, market_curves.port_area(economy.area_map, economy.setup.port_tile, COFFEE))


def port_price(economy: Economy) -> float:
    """The price the port market's last book clears at."""
    curve = economy.record.curves[port_key(economy)]
    return goods_market.clear(market_curves.bids_of(curve, COFFEE), market_curves.offers_of(curve, COFFEE),
                              COFFEE, market_curves.CURVE_AREA, "", None).price


def revenue_ceiling(economy: Economy) -> float:
    """The most coffee revenue the port market's buyers allow at any one price (from the last book)."""
    bids = market_curves.bids_of(economy.record.curves[port_key(economy)], COFFEE)
    best = 0.0
    price = 0.01
    while price < 100.0:
        best = max(best, price * sum(goods_market.quantity_at(bid, price) for bid in bids))
        price *= 1.05
    return best


def run_scenario(years: int = YEARS) -> List[Dict[str, float]]:
    """One row a year: price, volume at the port market, the entrant's and incumbents' capacity, the
    most revenue demand allows there."""
    setup = coffee_setup()
    economy = Economy(setup)
    rows = []
    for year in range(years):
        if year == ENTRY_YEAR:
            economy.setup.recipes[CHEAP.recipe_id] = CHEAP
            economy.record.producers[ENTRANT] = Producer(
                ENTRANT, sorted(economy.record.cohorts)[0], CHEAP.recipe_id, fixture.FARMS,
                START_CAPACITY_RUNS, expected_sales=START_CAPACITY_RUNS)
            economy.record.book.transfer(Transfer(EDGE_MINT, ENTRANT, setup.currency_id, 500.0, "stake"))
        elif year > ENTRY_YEAR and ENTRANT in economy.record.producers:
            entrant = economy.record.producers[ENTRANT]
            economy.record.producers[ENTRANT] = dataclasses.replace(
                entrant, capacity_runs=entrant.capacity_runs * CAPACITY_GROWTH_PER_YEAR)
        outcome = economy.step(fixture.quiet_year(setup))
        producers = economy.record.producers
        rows.append({
            "year": year, "price": outcome.prices.get(COFFEE, 0.0), "port_price": port_price(economy),
            "volume": economy.record.volumes.get(port_key(economy), 0.0),
            "entrant_runs": producers[ENTRANT].capacity_runs if ENTRANT in producers else 0.0,
            "incumbent_runs": sum(producer.capacity_runs for producer in producers.values()
                                  if producer.recipe_id == DEAR.recipe_id),
            "revenue_ceiling": revenue_ceiling(economy)})
    return rows
