"""The income the opening counts for the households against what the first years pay them: at the opening the sum of the
cohorts' income, its property part, the wage bill of the runs sized (hours of the sized runs at the opening's wages), the
cohorts' coin and the producers'; after each year the cohorts' income as the close leaves it, its property part, the wages
the year paid, the coin of both, and the producers' sales.
Usage: python3 opening_income_probe.py <civ> [years]"""
import random, sys
from sim.economy import api as economy_api
from sim.economy.api import EconomyYearInputs
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import port_sites

civ = sys.argv[1]
years = int(sys.argv[2]) if len(sys.argv) > 2 else 3
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
record = economy.record
money = setup.currency_id
book = record.book


def coin(agents):
    return sum(book.balance(agent_id, money) for agent_id in agents)


def line(label, wages=None, sales=None):
    cohorts = list(record.cohorts.values())
    income = sum(cohort.last_year_income for cohort in cohorts)
    prop = sum(record.capital_markets.property_income.get(cohort.agent_id, 0.0) for cohort in cohorts)
    print("%-10s cohorts' income %.4g (property %.4g, the rest %.4g)%s%s | coin: cohorts %.4g producers %.4g merchants %.4g" % (
        label, income, prop, income - prop,
        "" if wages is None else " | wages paid %.4g" % wages, "" if sales is None else " | producers' sales %.4g" % sales,
        coin(record.cohorts), coin(record.producers), coin(record.merchants)))


sized_bill = 0.0
for producer in record.producers.values():
    recipe = setup.recipes[producer.recipe_id]
    sized_bill += producer.expected_sales * sum(hours * setup.opening_wages.get(trade, 0.0) for trade, hours in recipe.labour_hours.items())
sized_value = sum(producer.expected_sales * sum(setup.opening_prices.get(good, 0.0) * quantity * producer.yield_factor
                                               for good, quantity in setup.recipes[producer.recipe_id].outputs.items())
                  for producer in record.producers.values())
line("opening")
print("           wage bill of the sized runs at the opening's wages %.4g; value of the sized output at the opening's prices %.4g" % (sized_bill, sized_value))
inputs = EconomyYearInputs(year=0, population_by_tile={}, yield_factor_by_producer=port_sites.crop_yields(economy), engine_orders={})
for year in range(years):
    outcome = economy.step(inputs)
    sales = sum(producer.revenue_history[-1] for producer in record.producers.values() if producer.revenue_history)
    line("year %d" % year, wages=outcome.hired_hours * (outcome.wages.get(setup.unskilled_trade) or 0.0), sales=sales)
