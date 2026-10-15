"""The agent economy's hidden first stage run for many years on a built game, one row per year.

`simulator.py spin-up-trace` prints it and the money-supply test reads it. It runs the stage as
`AgentEconomy._spin_up` does (a fresh economy in its spin-up, no player) on the opening the game saved, but
never stops at the tolerance, so a drift that the normal stage would cut short shows.
"""
from sim.economy import api as economy_api

from .economy_port_setup import build_setup
from .economy_port_year import YearInputs

COLUMNS = ("year", "price_level", "money_supply", "rate", "wear", "struck", "change", "metal_held", "wage", "hired_hours",
           "idle_hours")


def spin_up_trace(game, years):
    """[{year, price_level, money_supply, rate, wear, struck, change, metal_held, wage, hired_hours, idle_hours}]
    for `years` years of the
    first stage on the opening `game` saved. `wear` is the coin worn away that year, `struck` the coin the
    mint paid out net of what it melted, `change` the year's change in the money stock, `metal_held` the metal
    the mint holds at the year's end (economy units). `wage` is the unskilled trade's mean wage that year (economy
    units), `hired_hours` and `idle_hours` the hours employers took and the hours offered that nobody took."""
    setup = build_setup(game, game.state.economy.agent_economy["opening"])
    economy = economy_api.blank_economy(setup)
    economy_api.begin_spin_up(economy)
    inputs = YearInputs(year=0, population_by_tile={}, working_age_share=setup.working_share,
                        yield_factor_by_producer={}, engine_orders={})
    rows = []
    for year in range(years):
        outcome = economy.step(inputs)
        row = {"year": year, "price_level": outcome.basket_price_level, "money_supply": outcome.money_supply,
               "rate": outcome.rate, "wage": outcome.wages.get(setup.unskilled_trade, 0.0),
               "hired_hours": outcome.hired_hours, "idle_hours": outcome.idle_hours}
        row.update(economy_api.money_year_figures(economy, outcome))
        rows.append(row)
    return rows
