"""`spin-up-trace --fixture`: the hand-built three-tile economy (sim/economy/fixture_setups.py) stepped for quiet years,
one row per year, so a rule's effect on prices, wages, hours and money shows in seconds. `--rules` names the rule set it
runs on (sim/economy/rule_sets.py); `--twin` steps a second copy whose people differ by a rounding-sized share beside it
and adds how far apart the two are each year, which is how a rule that amplifies a small difference shows."""
import dataclasses

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


TWIN_NUDGE = 1e-9        # the share by which the twin's people on its first tile differ: the size of a rounding error
TWIN_GAP_COLUMN = "twin_gap"
TWIN_COMPARED = ("basket_price_level", "unskilled_wage", "hired_hours")


def quiet_year():
    """A year with the opening's people and no orders from outside."""
    return economy_api.EconomyYearInputs(year=0, population_by_tile={}, yield_factor_by_producer={}, engine_orders={})


def nudged(setup, share=TWIN_NUDGE):
    """`setup` with the people of its first tile (in name order) more by `share`."""
    people = dict(setup.opening_population_by_tile)
    first = min(people)
    people[first] *= 1.0 + share
    return dataclasses.replace(setup, opening_population_by_tile=people)


def largest_gap(row, other, columns=TWIN_COMPARED):
    """The largest difference between two years' rows over `columns`, each as a share of the first row's figure; a
    figure missing in either row, or nothing in the first, is left out, and no figure compared gives None."""
    gaps = [abs(row[name] - other[name]) / abs(row[name]) for name in columns
            if row.get(name) is not None and other.get(name) is not None and row[name] != 0.0]
    return max(gaps) if gaps else None


def fixture_trace(which, years, rules=None, twin=False, **changes):
    """The rows of `years` quiet years of the fixture named `which` (a key of FIXTURE_SETUPS), on the rule set `rules`
    (None: the setup's own); `changes` replace fields of its setup. With `twin`, a second copy (`nudged`) is stepped
    beside it and each row carries how far apart the two are (`TWIN_GAP_COLUMN`, `largest_gap`)."""
    setup = FIXTURE_SETUPS[which](**changes, **({} if rules is None else {"rule_set": rules}))
    economy = economy_api.blank_economy(setup)
    other = economy_api.blank_economy(nudged(setup)) if twin else None
    rows = []
    for year in range(years):
        row = fixture_row(economy, economy.step(quiet_year()), year, economy_api.labour_market_rows(economy))
        if other is not None:
            row[TWIN_GAP_COLUMN] = largest_gap(row, fixture_row(other, other.step(quiet_year()), year,
                                                                 economy_api.labour_market_rows(other)))
        rows.append(row)
    return rows


def columns_of(rows):
    """The trace's columns: the fixture's, and the twin gap where the rows carry one."""
    return FIXTURE_COLUMNS + ((TWIN_GAP_COLUMN,) if rows and TWIN_GAP_COLUMN in rows[0] else ())


def format_fixture_trace(rows):
    """The fixture trace as text: a header, then one line per year; a None cell shows as a dash. Each column is as
    wide as its name, and at least fourteen characters."""
    columns = columns_of(rows)
    widths = {name: max(14, len(name) + 1) for name in columns}
    lines = ["".join("%*s" % (widths[name], name) for name in columns)]
    for row in rows:
        lines.append("".join(_cell(row[name], widths[name]) for name in columns))
    return "\n".join(lines)


def _cell(value, width):
    if value is None:
        return "%*s" % (width, "-")
    return "%*d" % (width, value) if isinstance(value, int) else "%*.6g" % (width, value)
