"""Replays spin_up_run.spin_up on a civ's opening setup, without the early stop, and writes one JSON line per year:
stage, every spin_up_state quantity, rate, basket price level, unskilled wage, and all watched goods' prices.
Usage: python3 probe_spin.py <civ> <first_years> <trimmed_years> <out.jsonl>"""
import json
import random
import sys
import time

from sim.economy import api as economy_api
from sim.economy.api import EconomyYearInputs
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import port_sites
from sim.markets.spin_up_run import SPIN_UP_WATCHED_GOODS
from sim.markets.port_trace_holders import money_by_holder_columns

civ, first_years, trimmed_years, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
_tree, _prices, nodes, _wages, _goods = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
import os
if os.environ.get('ABLATE'):
    import ablations
    ablations.apply(os.environ['ABLATE'])
basket = economy_api.opening_quantities(economy)
prices = economy_api.opening_prices_of(economy)
watched = sorted(basket, key=lambda good: -basket[good] * prices.get(good, 0.0))[:int(SPIN_UP_WATCHED_GOODS)]
inputs = EconomyYearInputs(year=0, population_by_tile={}, yield_factor_by_producer=port_sites.crop_yields(economy), engine_orders={})
with open(out, "w") as handle:
    handle.write(json.dumps({"watched": watched, "opening_prices": {g: prices.get(g) for g in watched}}) + "\n")
    for stage, years in (("first", first_years), ("trimmed", trimmed_years)):
        if stage == "trimmed":
            economy_api.trim_workforce_to_expected_hours(economy)
        for year in range(years):
            started = time.time()
            outcome = economy.step(inputs)
            state = economy_api.spin_up_state(economy, outcome)
            row = {"stage": stage, "year": year, "seconds": round(time.time() - started, 1),
                   "price_level": outcome.basket_price_level, "rate": economy_api.interest_rate(economy),
                   "money_supply": outcome.money_supply,
                   "wage": outcome.wages.get(setup.unskilled_trade),
                   "prices": {good: outcome.prices.get(good) for good in watched}}
            row.update({key: value for key, value in state.items() if key not in ("prices",)})
            row.update(money_by_holder_columns(economy_api.economy_book(economy), economy_api.currency_id(economy)))
            row.update(economy_api.money_year_figures(economy, outcome))
            handle.write(json.dumps(row, default=float) + "\n")
            handle.flush()
