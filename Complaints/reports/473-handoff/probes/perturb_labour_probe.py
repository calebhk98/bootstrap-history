"""A perturbed spin-up's labour markets year by year: hours hired, the wage bill actually paid (hours times wage over all markets),
the hours-weighted wage, the unskilled wage reported, the money stock and the largest markets by wage bill.
Usage: python3 perturb_labour_probe.py <civ> none|price:<good>:<factor>|drop:<good> <years>"""
import dataclasses, random, sys
from sim.economy import api as economy_api, economy as economy_module
from sim.economy.api import EconomyYearInputs
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import port_sites

civ, change, years = sys.argv[1], sys.argv[2], int(sys.argv[3])
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
kind, _colon, rest = change.partition(":")
if kind == "price":
    good, _colon, factor = rest.partition(":")
    prices = dict(setup.opening_prices)
    prices[good] = prices[good] * float(factor)
    setup = dataclasses.replace(setup, opening_prices=prices)
captured = {}
original = economy_module.Economy._outcome
def patched(self, ledger, level, extraction, stocks_at_start):
    captured["results"] = [(result.trade, result.area, result.hours_hired, result.wage) for result in ledger.labour_results]
    captured["wages_in"] = sum(ledger.wages_in.values())
    return original(self, ledger, level, extraction, stocks_at_start)
economy_module.Economy._outcome = patched
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
money = setup.currency_id
print("opening: producers' coin %.4g, households' coin %.4g, hours sized %.4g" % (
    sum(economy.record.book.balance(p.agent_id, money) for p in economy.record.producers.values()),
    sum(economy.record.book.balance(c.agent_id, money) for c in economy.record.cohorts.values()),
    sum(p.expected_sales * sum(setup.recipes[p.recipe_id].labour_hours.values()) for p in economy.record.producers.values())))
inputs = EconomyYearInputs(year=0, population_by_tile={}, yield_factor_by_producer=port_sites.crop_yields(economy), engine_orders={})
for year in range(years):
    outcome = economy.step(inputs)
    results = captured["results"]
    hired = sum(row[2] for row in results)
    bill = sum(row[2] * row[3] for row in results)
    top = sorted(results, key=lambda row: -row[2] * row[3])[:3]
    print("yr %2d hired %.4g bill %.4g wages received %.4g mean wage %.4g unskilled %.4g money %.4g level %.4g | top: %s" % (
        year, hired, bill, captured["wages_in"], bill / hired if hired else 0.0, outcome.wages.get(setup.unskilled_trade) or 0.0, outcome.money_supply,
        outcome.basket_price_level, "; ".join("%s@%s %.3g h at %.3g" % (t, a.split("@")[-1], h, w) for t, a, h, w in top)))
