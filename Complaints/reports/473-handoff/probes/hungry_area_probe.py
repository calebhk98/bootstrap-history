"""One tile's food supply by year: its food makers (capacity, expected sales, runs worked), the merchants' routes into it
and the merchants' purses. Usage: python3 hungry_area_probe.py <civ> <tile> [years]"""
import random, sys
from collections import defaultdict
from sim.economy import api as economy_api
from sim.economy.api import EconomyYearInputs
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import port_sites

civ, tile = sys.argv[1], sys.argv[2]
years = int(sys.argv[3]) if len(sys.argv) > 3 else 8
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
money = setup.currency_id
hunger = setup.hunger_need
need = next(spec for spec in setup.basket_for(tile).needs if spec.need_id == hunger)
food = dict(need.goods)
people = sum(cohort.people for cohort in economy.record.cohorts.values() if cohort.tile == tile)
floor = need.subsistence_per_person * people
inputs = EconomyYearInputs(year=0, population_by_tile={}, yield_factor_by_producer=port_sites.crop_yields(economy), engine_orders={})

def makers():
    rows = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])
    for producer in economy.record.producers.values():
        if producer.tile != tile:
            continue
        recipe = setup.recipes[producer.recipe_id]
        per_run = sum(quantity * food[good] for good, quantity in recipe.outputs.items() if good in food) * producer.yield_factor
        if per_run <= 0.0:
            continue
        row = rows[producer.recipe_id]
        row[0] += producer.capacity_runs * per_run / floor
        row[1] += producer.expected_sales * per_run / floor
        row[2] += max(producer.last_runs, 0.0) * per_run / floor
        row[3] += 0.0 if producer.land_run_cap is None else producer.land_run_cap * per_run / floor
    return rows

print("tile", tile, "people %.0f" % people, "(figures are shares of the tile's food floor)")
print("opening:", " | ".join("%s cap %.3f exp %.3f" % (recipe, row[0], row[1]) for recipe, row in sorted(makers().items())))
for year in range(years):
    outcome = economy.step(inputs)
    print("year", year, "hunger here %.2f" % (outcome.hunger_by_tile.get(tile, 0.0) / floor))
    for recipe, row in sorted(makers().items()):
        print("     %-34s capacity %.3f expected %.3f worked %.3f land cap %.3f" % (recipe, row[0], row[1], row[2], row[3]))
    for key, merchant in economy.record.merchants.items():
        into = defaultdict(float)
        for (good, source), legs in merchant.routes.items():
            for leg in legs:
                if leg[0] == tile:
                    into[good] += leg[2]
        print("     %s cash %.4g routes %d into this tile: %s" % (key, economy.record.book.balance(merchant.agent_id, money), len(merchant.routes),
              " ".join("%s %.3g" % (good, weight) for good, weight in sorted(into.items()) if good in food)))
    print("     routes by length:", [(band.__dict__ if hasattr(band, "__dict__") else band) for band in outcome.merchant_routes][:4])
