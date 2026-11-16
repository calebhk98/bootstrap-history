import json, random, sys, time
from sim.economy import api as economy_api
from sim.economy.api import EconomyYearInputs
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import port_sites
civ, first_years, trimmed_years, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
_t,_p,nodes,_w,_g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
inputs = EconomyYearInputs(year=0, population_by_tile={}, yield_factor_by_producer=port_sites.crop_yields(economy), engine_orders={})
w = setup.opening_prices
with open(out, "w") as h:
    for stage, years in (("first", first_years), ("trimmed", trimmed_years)):
        if stage == "trimmed": economy_api.trim_workforce_to_expected_hours(economy)
        for year in range(years):
            outcome = economy.step(inputs)
            rec = economy.record
            held = {}
            for agent, prod in rec.producers.items():
                for good, bt in rec.book.holdings(agent)["goods"].items():
                    if good in w:
                        q = sum(bt.values())
                        if q: held.setdefault(good, {})[f"{agent}|{prod.recipe_id}|{prod.tile}"]=q
            row = {"stage": stage, "year": year, "rate": economy_api.interest_rate(economy), "market_rate": economy_api.market_rate(economy),
                   "price_level": outcome.basket_price_level,
                   "prices": {g: outcome.prices.get(g) for g in held}, "held": held,
                   "output": {g: q for g, q in outcome.output.items()}}
            h.write(json.dumps(row, default=float)+"\n"); h.flush()
            print(stage, year, row["rate"], flush=True)
h2 = open(out+".w","w"); json.dump(dict(w), h2)
