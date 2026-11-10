"""A small random economy for the year-arrays and close-kernel tests: recipes, producers, cohorts, a market memory, a book,
a ledger and an area map, built from a seed. No game is run."""
import random
import types

from sim.tests.credit_stub import credit_of

from sim.book import Book
from sim.economy.producer_store import ProducerStore
from sim.economy.households_cohort import Cohort
from sim.economy.market_memory import KEY_SEPARATOR, MarketMemory, YearView
from sim.economy.producers import Producer
from sim.economy.setup import labour_area
from sim.economy.types import (EDGE_MINT, ClearingResult, EDGE_PRODUCTION, QUOTE_BEST_UNFILLED_BID, QUOTE_COST_COVERING,
                               QUOTE_LOWEST_UNFILLED_ASK, QUOTE_OPENING_ESTIMATE, GoodSpec, GoodsMove, Loan, MarketArea,
                               Recipe, Transfer)
from sim.economy.year_ledger import YearLedger

GOODS = tuple("good%d" % each for each in range(7))
TRADES = ("labourer", "smith", "miller")
TILES = ("T0", "T1", "T2")
AREAS = {"north": ("T0", "T1"), "south": ("T2",)}
MONEY = "coin"


class AreaMapStub:
    def goods(self):
        return GOODS

    def areas(self, good):
        return tuple(MarketArea(area, good, tiles, tiles[0]) for area, tiles in AREAS.items())

    def area_of(self, good, tile):
        return "north" if tile in AREAS["north"] else "south"


def recipes_of(rng):
    recipes = {}
    for index in range(4):
        goods = rng.sample(GOODS, 5)
        plant = index % 2 == 0
        recipes["recipe%d" % index] = Recipe(
            "recipe%d" % index, {goods[0]: rng.uniform(1, 5), **({goods[1]: rng.uniform(1, 3)} if index == 1 else {})},
            {goods[2]: rng.uniform(0.5, 3), **({goods[3]: rng.uniform(0.5, 2)} if rng.random() < 0.5 else {})},
            {trade: rng.uniform(0.5, 4) for trade in rng.sample(TRADES, rng.randrange(1, 3))},
            {goods[4]: rng.uniform(1, 6)} if plant else {}, {"smith": rng.uniform(1, 5)} if plant else {},
            rng.uniform(5, 30) if plant else 0.0)
    return recipes


def setup_of(recipes):
    specs = {good: GoodSpec(good, 1.0 if index != 5 else float("inf"), 0.0 if index % 2 else 0.2, 0.0 if index % 3 else 8.0, "food")
             for index, good in enumerate(GOODS)}
    return types.SimpleNamespace(
        recipes=recipes, specs=specs, currency_id=MONEY, unskilled_trade="labourer",
        opening_wages={"labourer": 1.0, "smith": 3.0},
        trades={"labourer": types.SimpleNamespace(training_years=0.0), "smith": types.SimpleNamespace(training_years=5.0),
                "miller": types.SimpleNamespace(training_years=2.0)})


def memory_of(rng):
    memory = MarketMemory(rates={MONEY: 0.05}, year=3)
    kinds = (QUOTE_BEST_UNFILLED_BID, QUOTE_LOWEST_UNFILLED_ASK, QUOTE_COST_COVERING, QUOTE_OPENING_ESTIMATE)
    for good in GOODS:
        for area in AREAS:
            key = good + KEY_SEPARATOR + area
            if rng.random() < 0.85:
                memory.prices[key] = rng.uniform(0.5, 9.0)
                if rng.random() < 0.7:
                    memory.trade_age[key] = rng.choice((0, 0, 1, 2))
                if rng.random() < 0.5:
                    memory.quote_kinds[key] = rng.choice(kinds)
                if rng.random() < 0.4:
                    memory.cleared_prices[key] = memory.prices[key] * rng.uniform(0.8, 1.3)
    for trade in TRADES:
        for tile in TILES:
            if rng.random() < 0.6:
                memory.wages[trade + KEY_SEPARATOR + labour_area(tile)] = rng.uniform(0.5, 4.0)
    return memory


def economy_of(seed, producer_count=40):
    """(setup, record, view, ledger, area_map) of a random economy."""
    rng = random.Random(seed)
    recipes = recipes_of(rng)
    setup = setup_of(recipes)
    memory = memory_of(rng)
    book = Book()
    producers, cohorts, loans = {}, {}, []
    for index in range(producer_count):
        recipe = recipes["recipe%d" % rng.randrange(4)]
        agent = "producer:%03d" % index
        producers[agent] = Producer(
            agent, "household:T0:0", recipe.recipe_id, rng.choice(TILES), rng.uniform(5, 60), rng.uniform(0.6, 1.2),
            {good: rng.uniform(0.5, 8.0) for good in rng.sample(sorted(set(recipe.outputs) | set(recipe.inputs)), 1)},
            rng.choice((0, 0, 1, 4)), rng.uniform(0, 50), rng.choice((0.0, rng.uniform(1, 40))), rng.choice((-1.0, rng.uniform(0, 40))),
            rng.choice((0.0, 0.3)), None, 1, tuple(rng.sample((-5.0, 4.0, 20.0), rng.randrange(0, 2))),
            tuple(rng.sample((30.0, 50.0, 90.0), rng.randrange(0, 2))), rng.choice((0, 0, 0, 1)),
            rng.choice((None, rng.uniform(0, 30))))
        book.transfer(Transfer(EDGE_MINT, agent, MONEY, rng.uniform(0, 400), "seed"))
        for good in rng.sample(GOODS, 3):
            book.move(GoodsMove(EDGE_PRODUCTION, agent, good, rng.choice(TILES), rng.uniform(0, 60), "seed"))
        if rng.random() < 0.3:
            loans.append(Loan("loan:%d" % index, "lender", agent, MONEY, rng.uniform(5, 80), 0.06, rng.choice((1.0, 4.0)), 0.0,
                              arrears=rng.choice((0.0, 0.0, 3.0))))
    for tile in TILES:
        cohort = Cohort("household:%s:0" % tile, tile, 0, 100.0, 40.0, 1.0, share_wealth=None if tile == "T0" else 5.0)
        cohorts[cohort.agent_id] = cohort
    ledger = YearLedger()
    for agent, producer in producers.items():
        recipe = recipes[producer.recipe_id]
        ledger.sales_in[agent] = rng.uniform(0, 300)
        ledger.money_out[agent] = rng.uniform(0, 300)
        ledger.plant_spend[agent] = rng.choice((0.0, 5.0))
        ledger.hours_hired[agent] = {trade: rng.uniform(0, 100) for trade in recipe.labour_hours}
        for good in recipe.outputs:
            ledger.sold[(agent, good)] = rng.uniform(0, 80)
            ledger.output[(agent, good)] = rng.uniform(0, 100)
    for good in GOODS:
        for area in AREAS:
            if rng.random() < 0.6:
                ledger.unmet_demand[(good, area)] = rng.uniform(0, 50)
    for good in GOODS:
        for area in AREAS:
            traded = rng.choice((0.0, 5.0))
            ledger.note_clearing(ClearingResult(good, area, MONEY, rng.choice((None, rng.uniform(0.5, 9.0))), traded, 0.0, 0.0, ()), traded)
    record = types.SimpleNamespace(producers=ProducerStore(producers), cohorts=cohorts, memory=memory, book=book,
                                   credit=credit_of(loans))
    area_map = AreaMapStub()
    view = YearView(memory, book, area_map, MONEY, setup, labour_area)
    return setup, record, view, ledger, area_map
