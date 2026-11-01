"""The spin-up trace's macro columns, read from one year's `YearOutcome` and the labour markets' rows of that year
(`economy_api.labour_market_rows`), for a side-by-side with another model's monthly statistics (price level, average
wage, unemployment, real output)."""
from sim.economy import api as economy_api


def unemployment_columns(outcome, market_rows):
    """{unsold_hours_share, people_unemployment} for the year.

    `unsold_hours_share` is the share of hours offered on the labour markets that nobody hired, idle over hired plus
    idle (None when none was offered). It counts hours, so a household's hours that it puts to its plot anyway are in it.
    `people_unemployment` is the people-weighted share of the wage trades' people left without work
    (`person_equivalent_unemployment` over `market_rows`; None when no market offered hours)."""
    offered = outcome.hired_hours + outcome.idle_hours
    return {"unsold_hours_share": outcome.idle_hours / offered if offered > 0.0 else None,
            "people_unemployment": economy_api.person_equivalent_unemployment(market_rows)}


def macro_columns(outcome, unskilled_trade, real_output, market_rows):
    """{price_level, wage, real_output, unsold_hours_share, people_unemployment} for the year.

    `price_level` is the fixed-basket level against the index base (`basket_price_level`), not a chained index.
    `wage` is the unskilled trade's mean money wage per hour over the hours hired (None when the trade did not trade).
    `real_output` is the year's output valued at the opening prices (`spin_up_state`), passed in. The two unemployment
    figures are `unemployment_columns`, read from `market_rows`."""
    columns = {"price_level": outcome.basket_price_level,
               "wage": outcome.wages.get(unskilled_trade),
               "real_output": real_output}
    columns.update(unemployment_columns(outcome, market_rows))
    return columns
