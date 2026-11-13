"""The hidden spin-up replayed as `spin_up_run.spin_up` runs it, year by year, for `spin-up-trace --stages`: the first
stage for its full years without the early stop, the workforce trim, then the trimmed stage. Each year's row holds the
state the settle test measures (spin_up_year.year_state) with the macro and money figures beside it. Only reads."""
from sim.economy import api as economy_api

from .port_trace_holders import money_by_holder_columns
from .spin_up import SPIN_UP_MEASURED_YEARS, spin_up_years
from .spin_up_gap import window_gaps, worst_price_change
from .spin_up_year import watched_goods, year_inputs, year_state


def replay(economy, inputs, watched, unskilled_trade, first_years, trimmed_years):
    """Yield one row per year: the first stage's `first_years` years, then (after the workforce is trimmed to the hours
    employers want, as the run does) the trimmed stage's `trimmed_years`. A row is {stage, year, money_supply, wage,
    money by holder, the year's money figures, and year_state's price_level, rate, prices and settle quantities}."""
    for stage, years in (("first", first_years), ("trimmed", trimmed_years)):
        if stage == "trimmed":
            economy_api.trim_workforce_to_expected_hours(economy)
        for year in range(years):
            outcome = economy.step(inputs)
            row = {"stage": stage, "year": year, "money_supply": outcome.money_supply,
                   "wage": outcome.wages.get(unskilled_trade)}
            row.update(year_state(economy_api.spin_up_state(economy, outcome), outcome.basket_price_level,
                                  economy_api.interest_rate(economy), outcome.prices, watched))
            row.update(money_by_holder_columns(economy_api.economy_book(economy), economy_api.currency_id(economy)))
            row.update(economy_api.money_year_figures(economy, outcome))
            yield row


def replay_opening(setup):
    """(watched goods, the rows' generator) for the full-length spin-up of the opening `setup`, on a fresh economy."""
    economy = economy_api.blank_economy(setup)
    economy_api.begin_spin_up(economy)
    watched = watched_goods(economy)
    first_years, trimmed_years = spin_up_years()
    return watched, replay(economy, year_inputs(economy), watched, setup.unskilled_trade, first_years, trimmed_years)


def end_gaps(rows, measured_years=None):
    """What the opening reports of the rows: {"gaps": window_gaps of the last `measured_years` (default
    SPIN_UP_MEASURED_YEARS) trimmed rows, as spin_up_run.final_result computes it (None when fewer than two),
    "measured_years", "worst_price": (the watched good with the largest change in them, that change)}."""
    count = int(SPIN_UP_MEASURED_YEARS) if measured_years is None else measured_years
    states = [row for row in rows if row["stage"] == "trimmed"][-count:]
    return {"gaps": window_gaps(states), "measured_years": len(states), "worst_price": worst_price_change(states)}
