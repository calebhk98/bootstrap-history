"""Complaint 442, whole game: the price of gold against silver follows the stocks and where the mines are.

Slow topic: it builds a game per civilisation and steps it. It prints the gold-to-silver price ratio at
the capital each year (the re-measure of Complaint 442), the deposits left out of each opening stock, and
what the state and the households hold of each metal, so the check is one command:
`python3 -m sim.tests --slow --only whole_game_gold_silver_ratio`.

The only hard check is the physical one: where both metals trade, a kilogram of gold is dearer than a
kilogram of silver (a ratio below one is a bug). The size of the ratio is measured, not asserted."""
from .harness import *  # noqa: F401,F403

import statistics

from sim.engine.economy_port_stores import opening_store_values
from sim.geography.api import open_map, tiles_held

GOLD, SILVER = "gold_kg", "silver_kg"
YEARS = 30
CIVILISATIONS = ("rome_100ad", "england_1300", "han_china_100ad", "norse_900ad", "mexica_1500")


def held_value(record, agent, good, price):
    return sum(record.book.holdings(agent)["goods"].get(good, {}).values()) * (price or 0.0)


def run(civ):
    game = S.Sim(NODES, ORDER, random.Random(1), events=True, manual=False, civ=S.load_civ(civ),
                 cfg={"agent_economy": True})
    game.goal, game.done_year = GOAL, {}
    economy = game.economy.agent.economy()
    setup, record = economy.setup, economy.record
    ratios = []
    for _year in range(YEARS):
        game.step()
        view = economy.view()
        prices = {good: view.price(good, economy.area_map.area_of(good, setup.capital_tile)) for good in (GOLD, SILVER)}
        if prices[GOLD] and prices[SILVER]:
            ratios.append(prices[GOLD] / prices[SILVER])
    return economy, ratios


for civ_id in CIVILISATIONS:
    economy, ratios = run(civ_id)
    setup, record = economy.setup, economy.record
    median = statistics.median(ratios) if ratios else float("nan")
    print("MEASURE %s: gold to silver price ratio at the capital, median %.2f over %d years with both priced "
          "(min %.2f, max %.2f)" % (civ_id, median, len(ratios), min(ratios, default=float("nan")),
                                     max(ratios, default=float("nan"))))
    view = economy.view()
    for good in (GOLD, SILVER):
        price = view.price(good, economy.area_map.area_of(good, setup.capital_tile))
        print("MEASURE %s: %s state holds %.0f in value, households hold %.0f"
              % (civ_id, good, held_value(record, setup.state_agent, good, price),
                 sum(held_value(record, cohort.agent_id, good, price) for cohort in record.cohorts.values())))
    check("%s: where both metals trade, gold costs more per kilogram than silver" % civ_id,
          all(ratio > 1.0 for ratio in ratios), [round(ratio, 2) for ratio in ratios if ratio <= 1.0][:5])

world_map = open_map()
for civ_id in CIVILISATIONS:
    civ = S.load_civ(civ_id)
    stores = opening_store_values(world_map, tiles_held(civ, world_map), int(civ["year"]))
    for good in (GOLD, SILVER):
        row = stores.get(good, {"workings": [], "gap": "no resource yields it"})
        print("MEASURE %s: opening store of %s counts %d workings; left out: %s"
              % (civ_id, good, len(row["workings"]), row["gap"] or "nothing"))
