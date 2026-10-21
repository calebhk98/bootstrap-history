"""Scenario: Complaints/507 stage 5 in a game. What an entry costs a producer is the calculator at the economy's prices, wages,
rate and rent: the cost book of a game costs an incumbent entry, its ratio against itself is one, and the cost moves with the
economy's input prices and wages (not with the long-run table). The rules (running below full cost, dearer inputs and wages
dearer making) are in test_entry_cost_at_economy_prices."""
from .harness import *  # noqa: F401,F403

from sim.engine import prices as price_solver
from sim.engine.economy_cost_book import economy_cost_book

game = sim(civ="rome_100ad", capital=5_000_000.0)
production = price_solver.default_production_entries()
home_prices = game.goods_market.household_prices


def a_plant_bearing_entry():
    """(entry key, material) of an entry the incumbents run that has a plant, an input and labour, and costs."""
    book = economy_cost_book(game)
    for key in sorted(production):
        entry = production[key]
        if not (entry.get("capital") and entry.get("inputs") and entry.get("labour_hours") and entry.get("outputs")):
            continue
        material = sorted(entry["outputs"])[0]
        if game._reference_entry(material) == key and book.unit_cost(key, material) and \
                book.running_unit_cost(key, material) is not None:
            return key, material
    return None, None


entry_key, material = a_plant_bearing_entry()
check("an incumbent entry with a plant, an input and labour can be costed at the economy's prices",
      entry_key is not None)
book = economy_cost_book(game)
full, running = book.unit_cost(entry_key, material), book.running_unit_cost(entry_key, material)
check("a plant that exists offers at its running cost, below the full cost a new one is judged at",
      0.0 < running < full, (running, full))
check("the incumbents' own entry costs the same as itself: ratio one at full cost",
      abs(game.entry_cost_ratio(entry_key, material) - 1.0) < 1e-9, game.entry_cost_ratio(entry_key, material))
check("...and its running ratio is below one",
      game.entry_cost_ratio(entry_key, material, running=True) < 1.0)
check("...and is the running cost over the full cost",
      abs(game.entry_cost_ratio(entry_key, material, running=True) - running / full) < 1e-9)

# the cost reads the economy's prices: dearer inputs, dearer making
inputs = set(production[entry_key]["inputs"])
check("the entry's inputs have prices at the economy", all(home_prices().get(good) for good in inputs))
real_prices = game.goods_market.household_prices
game.goods_market.household_prices = lambda: {good: price * (2.0 if good in inputs else 1.0)
                                              for good, price in real_prices().items()}
dearer_inputs = economy_cost_book(game).unit_cost(entry_key, material)
game.goods_market.household_prices = real_prices
check("dearer inputs at the economy raise the cost of making", dearer_inputs > full, (dearer_inputs, full))

# ...and so do dearer wages
real_wage = game.economy.agent_wage_per_hour
game.economy.agent_wage_per_hour = lambda trade: 2.0 * (real_wage(trade) or game.labour.market.quote(trade))
dearer_labour = economy_cost_book(game).unit_cost(entry_key, material)
game.economy.agent_wage_per_hour = real_wage
check("dearer wages at the economy raise the cost of making", dearer_labour > full, (dearer_labour, full))
check("the cost book is remembered while the economy's prices stand",
      game._cost_book() is game._cost_book())
