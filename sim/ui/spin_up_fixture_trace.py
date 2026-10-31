"""`spin-up-trace --fixture`: the hand-built three-tile economy (sim/economy/fixture_setups.py) stepped for quiet years,
one row per year, so a rule's effect on prices, wages, hours and money shows in under a second."""
from sim.economy import api as economy_api
from sim.markets.port_trace_columns import unemployment_columns
from sim.markets.port_trace_holders import HOLDER_COLUMNS, money_by_holder_columns

FIXTURE_SETUPS = {"small": economy_api.fixture_small_setup, "stationary": economy_api.fixture_stationary_setup}
FIXTURE_COLUMNS = ("year", "basket_price_level", "unskilled_wage", "staple_price", "real_wage", "hired_hours",
                   "idle_hours", "unsold_hours_share", "people_unemployment", "rate", "money_supply", "hunger") + HOLDER_COLUMNS


def fixture_row(economy, outcome, year, market_rows):
    """One year's row: the basket price level, the unskilled wage, the staple's price, the real wage (wage over
    that price; None when either is missing or the price is not positive), the hours hired and idle, the two
    unemployment figures (`unemployment_columns`), the rate, the money stock, hunger summed over the tiles, and the money
    each kind of holder keeps (HOLDER_COLUMNS). Prices and wages the outcome does not carry are None."""
    wage = outcome.wages.get(economy_api.FIXTURE_UNSKILLED_TRADE)
    staple_price = outcome.prices.get(economy_api.FIXTURE_STAPLE)
    real_wage = wage / staple_price if wage is not None and staple_price is not None and staple_price > 0.0 else None
    row = {"year": year, "basket_price_level": outcome.basket_price_level, "unskilled_wage": wage,
           "staple_price": staple_price, "real_wage": real_wage, "hired_hours": outcome.hired_hours,
           "idle_hours": outcome.idle_hours, "rate": outcome.rate, "money_supply": outcome.money_supply,
           "hunger": sum(outcome.hunger_by_tile.values())}
    row.update(unemployment_columns(outcome, market_rows))
    row.update(money_by_holder_columns(economy.record.book, economy.setup.currency_id))
    return row


def fixture_trace(which, years):
    """The rows of `years` quiet years of the fixture named `which` (a key of FIXTURE_SETUPS)."""
    setup = FIXTURE_SETUPS[which]()
    economy = economy_api.blank_economy(setup)
    rows = []
    for year in range(years):
        inputs = economy_api.YearInputs(year=0, population_by_tile={}, working_age_share=setup.working_share,
                                        yield_factor_by_producer={}, engine_orders={})
        outcome = economy.step(inputs)
        rows.append(fixture_row(economy, outcome, year, economy_api.labour_market_rows(economy)))
    return rows


def format_fixture_trace(rows):
    """The fixture trace as text: a header, then one line per year; a None cell shows as a dash. Each column is as
    wide as its name, and at least fourteen characters."""
    widths = {name: max(14, len(name) + 1) for name in FIXTURE_COLUMNS}
    lines = ["".join("%*s" % (widths[name], name) for name in FIXTURE_COLUMNS)]
    for row in rows:
        lines.append("".join(_cell(row[name], widths[name]) for name in FIXTURE_COLUMNS))
    return "\n".join(lines)


def _cell(value, width):
    if value is None:
        return "%*s" % (width, "-")
    return "%*d" % (width, value) if isinstance(value, int) else "%*.6g" % (width, value)
