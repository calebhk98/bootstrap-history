"""The opening's household purse against the first year's spending rule, cohort by cohort and in total: the coin, income and
share wealth the opening gives, the income the first year pays, and what households_buffer_stock.spending_budget makes of them.
Usage: python3 purse_probe.py <civ>"""
import random, sys
from sim.economy import api as economy_api, households_buffer_stock as rule, opening_resting
from sim.economy.api import EconomyYearInputs
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import port_sites

civ = sys.argv[1]
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
money = setup.currency_id
record = economy.record
before = {key: (record.book.balance(cohort.agent_id, money), cohort.last_year_income, cohort.share_wealth or 0.0, cohort.people,
                record.capital_markets.property_income.get(cohort.agent_id, 0.0))
          for key, cohort in record.cohorts.items()}
inputs = EconomyYearInputs(year=0, population_by_tile={}, yield_factor_by_producer=port_sites.crop_yields(economy), engine_orders={})
economy.step(inputs)
share = rule.yearly_cash_share()
months = rule.WEALTH_INCOME_RATIO_TARGET / rule.MONTHS_PER_YEAR
totals = [0.0] * 9
rows = []
for key, cohort in record.cohorts.items():
    cash, opening_income, shares, people, property_income = before[key]
    income = cohort.last_year_income                      # what the first year paid it
    planned = cohort.expected_spending                    # the first year seeds it with the larger of spent and planned
    mean_income = rule.mean_net_income(income, opening_income)
    cash_at_orders = cash + income - property_income      # the purse counts the wages as in hand; property income came at the last close
    budget = rule.spending_budget(mean_income, cash_at_orders, shares)
    resting = opening_resting.resting_household_purse(opening_income, shares)
    row = (cash, opening_income, income, shares, months * mean_income, budget, planned, resting, property_income)
    rows.append((key, people) + row)
    for place, value in enumerate(row):
        totals[place] += value
names = ("coin at opening", "income the opening assumed", "income year one paid", "share wealth", "wealth target", "rule's budget", "planned (seeded expected spending)", "purse with no plot", "property income")
for name, value in zip(names, totals):
    print("%-38s %.4g" % (name, value))
print("yearly share of wealth spent %.4f; target months %.2f" % (share, rule.WEALTH_INCOME_RATIO_TARGET))
print("largest cohorts: key, people, coin, assumed income, paid income, shares, target, budget, planned")
for row in sorted(rows, key=lambda row: -row[2])[:6]:
    print("   %-28s %8.0f " % row[:2] + " ".join("%9.3g" % value for value in row[2:9]))
