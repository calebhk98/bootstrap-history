"""The agent economy's hidden years from its opening until prices and the interest rate settle. Part of the port.

The same opening always gives the same record, so it is cached on disk with the price solver's results (keyed on the
data files and on the source this module can reach, port_key.SPIN_UP_SOURCE_MODULES)."""
import collections

from sim.agents.api import PURSE_CURRENCY
from sim.economy import api as economy_api
from sim.prices.api import solve_cache

from .port_key import spin_up_key
from .port_trace import TraceRows
from .spin_up_trace_cache import keep_trace
from .spin_up import (SPIN_UP_CACHE_DIRECTORY, SPIN_UP_MAXIMUM_YEARS, SPIN_UP_MEASURED_YEARS, SPIN_UP_TOLERANCE,
                      SPIN_UP_TRIMMED_YEARS, spin_up_years)
from .spin_up_year import SPIN_UP_WATCHED_GOODS, watched_goods, year_inputs, year_state   # the first is read from here by the tools
from .spin_up_gap import SPIN_UP_RATE_FLOOR, change_gap, price_gap, unsettled_cause, window_gaps

def spin_up_cache_key(setup):
    years = spin_up_years()
    return spin_up_key(setup, None if years == (int(SPIN_UP_MAXIMUM_YEARS), int(SPIN_UP_TRIMMED_YEARS)) else years)


def record_for(setup):
    """The record of the economy after the hidden years on `setup`, from the disk cache when it holds it."""
    return solve_cache.cached_json(spin_up_cache_key(setup), lambda: spun_up(setup), cache_dir=SPIN_UP_CACHE_DIRECTORY)


def spun_up(setup):
    """The record after the hidden years, run on a fresh economy. A full-length spin-up whose first stage runs to its
    bound keeps that stage's trace too (spin_up_trace_cache.py), so the opening checks need not run it again."""
    economy = economy_api.blank_economy(setup)
    economy_api.begin_spin_up(economy)
    full_length = spin_up_years() == (int(SPIN_UP_MAXIMUM_YEARS), int(SPIN_UP_TRIMMED_YEARS))
    trace = TraceRows(setup) if full_length else None
    spin_up(economy, trace)
    if trace is not None and len(trace.rows) == int(SPIN_UP_MAXIMUM_YEARS):
        keep_trace(setup, trace.rows)
    return economy_api.export_record(economy, (PURSE_CURRENCY,))


def spin_up(economy, trace=None):
    """Hidden years from the opening until prices and the interest rate settle; then the price level is rebased to one.
    `trace` (port_trace.TraceRows), when given, gets a row for each first-stage year."""
    watched = watched_goods(economy)
    inputs = year_inputs(economy)
    first_stage = settle(economy, inputs, watched, trace)
    economy_api.trim_workforce_to_expected_hours(economy)
    final_states = settle_trimmed(economy, inputs, watched)
    economy_api.trim_workforce_to_expected_hours(economy)   # the trade the settled years left idle does not carry its people into the game
    economy_api.finish_spin_up(economy)
    years = first_stage["years"] + spin_up_years()[1]
    economy_api.note_spin_up_result(economy, final_result(first_stage, final_states, years))


def settle(economy, inputs, watched, trace=None):
    """The first stage's stop rule (it decides when the stage ends; it is not the opening's reported
    result): hidden years until the price level, the rate (against a floor, see spin_up_gap) and the main
    prices move less than the tolerance a year. Returns {"settled": whether the tolerance was met, "years":
    years run, "gap": the largest change in the last year measured (none measured: infinity is not stored,
    so one)}."""
    before = None
    gap = 1.0
    years = 0
    settled = False
    for _year in range(spin_up_years()[0]):
        outcome = economy.step(inputs)
        years += 1
        if trace is not None:
            trace.add(economy, outcome)
        now = (outcome.basket_price_level, economy_api.interest_rate(economy),
               {good: outcome.prices[good] for good in watched if outcome.prices.get(good) is not None})
        if before is not None:
            gap = max(change_gap(now[0], before[0]) if before[0] > 0.0 else 0.0,
                      change_gap(now[1], before[1], SPIN_UP_RATE_FLOOR)
                      if now[1] is not None and before[1] is not None and before[1] > 0.0 else 0.0,     # no rate: no rate gap
                      price_gap(now[2], before[2]))
            if gap < SPIN_UP_TOLERANCE:
                settled = True
                break
        before = now
    return {"settled": settled, "years": years, "gap": gap}


def settle_trimmed(economy, inputs, watched):
    """The few further years, from the state the first stage left, in which the trimmed trades' wages and
    entry settle. Returns the state (see spin_up_gap) of each of the last SPIN_UP_MEASURED_YEARS years."""
    states = collections.deque(maxlen=int(SPIN_UP_MEASURED_YEARS))
    for _year in range(spin_up_years()[1]):
        outcome = economy.step(inputs)
        states.append(year_state(economy_api.spin_up_state(economy, outcome), outcome.basket_price_level,
                                 economy_api.interest_rate(economy), outcome.prices, watched,
                                 economy_api.traded_price_goods(economy)))
    return list(states)


def final_result(first_stage, final_states, years):
    """What the saved opening reports, apart from the stop rule: whether the state it opens in (after
    trimming) moved less than the tolerance a year, in every quantity spin_up_gap measures, over the last
    consecutive years and `spin_up_gap.unsettled_cause` finds none. {"settled", "years" (all hidden years), "gap" (largest
    change; one when fewer than two years were measured), "cause" (why not settled whatever the gap, or None),
    "unmeasured" (the last year's watched goods left out as no trade, with causes), "gaps" (by quantity), "measured_years", "final" (the last year's state),
    "first_stage" (the stop rule's own result)}."""
    gaps = window_gaps(final_states)
    gap = 1.0 if gaps is None else max(gaps.values())
    cause = unsettled_cause(final_states)
    return plain({"settled": cause is None and gap < SPIN_UP_TOLERANCE, "years": years, "gap": gap, "cause": cause,
                  "unmeasured": dict(final_states[-1].get("unmeasured", {})) if final_states else {},
                  "gaps": gaps or {}, "measured_years": len(final_states),
                  "final": dict(final_states[-1]) if final_states else {}, "first_stage": dict(first_stage)})


def plain(value):
    """`value` with numpy scalars made Python numbers and booleans: the result is saved as JSON, which takes neither a
    numpy boolean nor a numpy integer (the measured quantities come from kernels)."""
    if isinstance(value, dict):
        return {key: plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return type(value)(plain(item) for item in value)
    if hasattr(value, "item") and type(value).__module__ == "numpy":
        return value.item()
    return value
