"""The agent economy's hidden first stage run for many years on a built game, one row per year.

`simulator.py spin-up-trace` prints it and the money-supply test reads it. It runs the stage as
`AgentEconomy._spin_up` does (a fresh economy in its spin-up, no player) on the opening the game saved, but
never stops at the tolerance, so a drift that the normal stage would cut short shows.
"""
from sim.economy import api as economy_api

from . import port_sites
from .port_setup import build_setup
from .port_trace_chained import next_chained_index
from .port_trace_columns import macro_columns
from .port_trace_holders import HOLDER_COLUMNS, money_by_holder_columns
from .port_year import YearInputs

COLUMNS = ("year", "price_level", "money_supply", "rate", "wear", "struck", "change", "metal_held", "wage", "hired_hours",
           "idle_hours", "unsold_hours_share", "people_unemployment", "real_output", "chained_price_level") + HOLDER_COLUMNS


def spin_up_trace(game, years):
    """[{year, price_level, money_supply, rate, wear, struck, change, metal_held, wage, hired_hours, idle_hours,
    unsold_hours_share, people_unemployment, real_output, chained_price_level, and HOLDER_COLUMNS}] (the macro columns from
    port_trace_columns.py, then
    `chained_price_level`: 1 in the first year, then each year's prices over the last year's at this year's output,
    port_trace_chained.py; the money each kind of holder keeps, port_trace_holders.py) for `years` years of the
    first stage on the opening `game` saved. `wear` is the coin worn away that year, `struck` the coin the
    mint paid out net of what it melted, `change` the year's change in the money stock, `metal_held` the metal
    the mint holds at the year's end (economy units). `wage` is the unskilled trade's mean wage that year (economy
    units), `hired_hours` and `idle_hours` the hours employers took and the hours offered that nobody took."""
    world = game.view("legacy_economy")().world
    setup = build_setup(world, world.agent_record()["opening"])
    economy = economy_api.blank_economy(setup)
    economy_api.begin_spin_up(economy)
    inputs = YearInputs(year=0, population_by_tile={}, working_age_share=setup.working_share,
                        yield_factor_by_producer=port_sites.crop_yields(economy), engine_orders={})
    rows = []
    chained, previous_prices = 1.0, None
    for year in range(years):
        outcome = economy.step(inputs)
        row = {"year": year, "price_level": outcome.basket_price_level, "money_supply": outcome.money_supply,
               "rate": outcome.rate,
               "hired_hours": outcome.hired_hours, "idle_hours": outcome.idle_hours}
        row.update(macro_columns(outcome, setup.unskilled_trade, economy_api.spin_up_state(economy, outcome)["real_output"],
                                 economy_api.labour_market_rows(economy)))
        if previous_prices is not None:
            chained = next_chained_index(chained, previous_prices, outcome.prices, outcome.output)
        previous_prices = dict(outcome.prices)
        row["chained_price_level"] = chained
        row.update(economy_api.money_year_figures(economy, outcome))
        row.update(money_by_holder_columns(economy.record.book, economy.setup.currency_id))
        rows.append(row)
    return rows


def sensitivity_table(game, years, skip, variants=None):
    """One line per variant of how the economy adjusts (economy_api.spin_up_sensitivity.VARIANTS, or the names in
    `variants`): the price level's and the wage's drift, cycle amplitude and period over the first stage on `game`'s
    opening, the first `skip` years left out. One spin-up per variant."""
    sensitivity = economy_api.spin_up_sensitivity

    def series_of(variant, count):
        with sensitivity.VARIANTS[variant]():
            rows = spin_up_trace(game, count)
        return [row["price_level"] for row in rows], [row["wage"] for row in rows]

    return sensitivity.table(series_of, years, skip, variants)


def coin_wear_per_year():
    """Share of the coin stock worn away in a year, as the economy applies it."""
    return economy_api.COIN_WEAR_PER_YEAR


def traded_staple(agent, stale):
    """The good of the hunger need with the largest opening basket quantity among those whose markets cleared
    lately (a good nobody trades shows what it would cost to make, not a price); None when none did."""
    economy = agent.economy()
    setup = economy.setup
    need = next((spec for spec in setup.basket.needs if spec.need_id == setup.hunger_need), None)
    opening = economy_api.opening_quantities(economy)
    goods = [good for good, _effect in need.goods if good not in stale] if need is not None else []
    return max(goods, key=lambda good: opening.get(good, 0.0), default=None)
