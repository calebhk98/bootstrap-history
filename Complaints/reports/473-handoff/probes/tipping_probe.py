"""One ensemble member through the first-stage years: by year the hunger of each tile, and for the staple's makers and its
processors in the largest area their capacity, expected sales and runs worked (as shares of the opening's), the staple's
delivered and unmet volume there, and the area's unskilled wage. Writes one JSON line a year.
Usage: python3 tipping_probe.py <civ> <member> <years> <out.jsonl> <good> [<good> ...]"""
import json, random, sys
from collections import defaultdict
from sim.economy import api as economy_api
from sim.economy.market_memory import market_key
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import spin_up_stages
from sim.markets.spin_up_ensemble import cash_factor

civ, member, years, out, goods = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5:]
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
if cash_factor(member) != 1.0:
    spin_up_stages.perturb_household_cash(economy, cash_factor(member))
inputs = spin_up_stages.year_inputs(economy)
area_map = setup.area_map()
record = economy.record
hunger = setup.hunger_need
need = next(spec for spec in setup.basket_for(setup.capital_tile).needs if spec.need_id == hunger)
people = defaultdict(float)
for cohort in record.cohorts.values():
    people[cohort.tile] += cohort.people
money = setup.currency_id

def recipes_state():
    rows = defaultdict(lambda: [0.0, 0.0, 0.0, 0])
    for producer in record.producers.values():
        recipe = setup.recipes[producer.recipe_id]
        if not any(good in recipe.outputs for good in goods):
            continue
        row = rows[producer.recipe_id]
        row[0] += producer.capacity_runs
        row[1] += producer.expected_sales
        row[2] += max(producer.last_runs, 0.0)
        row[3] += 1
    return {recipe: row for recipe, row in rows.items()}

with open(out, "w") as handle:
    handle.write(json.dumps({"year": -1, "recipes": recipes_state()}, default=float) + "\n")
    for year in range(years):
        outcome = economy.step(inputs)
        markets = {}
        for good in goods:
            for area in area_map.areas(good):
                key = market_key(good, area.area_id)
                markets[key] = [record.goods.volumes.get(key, 0.0) or 0.0, record.goods.unmet.get(key, 0.0) or 0.0, record.goods.unsold.get(key, 0.0) or 0.0,
                                record.memory.prices.get(key), record.memory.price_kind(key)]
        cash = defaultdict(float)
        income = defaultdict(float)
        for cohort in record.cohorts.values():
            cash[cohort.tile] += record.book.balance(cohort.agent_id, money)
            income[cohort.tile] += cohort.last_year_income
        handle.write(json.dumps({"year": year, "hunger": {tile: outcome.hunger_by_tile.get(tile, 0.0) / (need.subsistence_per_person * people[tile]) for tile in people},
                                 "cash": {tile: cash[tile] / people[tile] for tile in people}, "income": {tile: income[tile] / people[tile] for tile in people},
                                 "recipes": recipes_state(), "markets": markets, "wages": dict(outcome.wages), "prices": {good: outcome.prices.get(good) for good in goods},
                                 "hired_hours": outcome.hired_hours, "producer_cash": sum(record.book.balance(producer.agent_id, money) for producer in record.producers.values()),
                                 "household_cash": sum(cash.values())}, default=float) + "\n")
        handle.flush()
