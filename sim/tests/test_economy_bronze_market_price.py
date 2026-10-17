"""Complaint 502: in an aged Rome game bronze, whose recipe is a melt of copper and tin with fuel and a few
skilled hours, shows (and trades at) a bounded multiple of what that recipe costs at the live input prices and
wages, not the price one thin market's remembered ask and budget bids settled on."""
from .harness import *  # noqa: F401,F403

from sim.economy import api as economy_api
from sim.economy import notional
from sim.economy.protocols import YearInputs
from sim.economy.national_prices import national_prices

# Eighteen engine years stepped by hand (about nine seconds each, mostly merchant route search in
# `sim/economy/merchants.py`); the allowance retires when a year costs a fraction of that.
TOPIC_SECONDS = 360
GOOD = "bronze_kg"
YEARS_PLAYED = 18
MARKUP_BOUND = 3.0      # a melt's fuel and skilled hours are already in its recipe cost; a markup beyond this is a thin market


def bronze_multiples(years):
    """(year, shown price, traded market price) of bronze over its recipe cost at the shown prices, for each year
    of Rome's agent economy stepped on its own (no engine orders)."""
    game = S.Sim(NODES, ORDER, random.Random(1), events=True, manual=False, civ=S.load_civ("rome_100ad"))
    economy = game.economy.agent.economy()
    rows = []
    for year in range(years):
        economy.step(YearInputs(year=year, population_by_tile={}, working_age_share=0.6,
                                yield_factor_by_producer={}, engine_orders={}))
        record = economy.record
        shown, _stale = economy_api.shown_prices_of(economy)
        cost = notional.cheapest_cost(economy.setup, GOOD, shown, notional.mean_wages(record.memory),
                                      record.memory.rates.get(economy.setup.currency_id, 0.0))
        rows.append((year + 1, shown[GOOD] / cost, national_prices(record)[GOOD] / cost))
    return rows


def aged_bronze_is_priced_near_its_recipe():
    rows = bronze_multiples(YEARS_PLAYED)
    worst_shown = max(row[1] for row in rows)
    worst_traded = max(row[2] for row in rows)
    return (worst_shown <= MARKUP_BOUND and worst_traded <= MARKUP_BOUND,
            "shown/cost worst %.2f, traded/cost worst %.2f, by year %s" % (
                worst_shown, worst_traded, [(year, round(shown, 2), round(traded, 2)) for year, shown, traded in rows]))


slow_check("Complaint 502: bronze in an aged Rome game shows and trades within a bounded multiple of its recipe cost",
           aged_bronze_is_priced_near_its_recipe)
