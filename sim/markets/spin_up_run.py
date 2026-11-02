"""The agent economy's hidden years from its opening until prices and the interest rate settle. Part of the port.

The same opening always gives the same record, so it is cached on disk with the price solver's results (keyed on the
data files and on the source this module can reach, port_key.SPIN_UP_SOURCE_MODULES)."""
import collections

from sim.agents.api import PURSE_CURRENCY
from sim.economy import api as economy_api
from sim.economy.api import YearInputs
from sim.prices.api import solve_cache

from . import port_sites
from .port_key import spin_up_key
from .spin_up import (SPIN_UP_CACHE_DIRECTORY, SPIN_UP_MAXIMUM_YEARS, SPIN_UP_MEASURED_YEARS, SPIN_UP_TOLERANCE,
                      SPIN_UP_TRIMMED_YEARS, spin_up_years)
from .spin_up_gap import SPIN_UP_RATE_FLOOR, change_gap, price_gap, window_gaps

SPIN_UP_WATCHED_GOODS = 12


def spin_up_cache_key(setup):
    years = spin_up_years()
    return spin_up_key(setup, None if years == (int(SPIN_UP_MAXIMUM_YEARS), int(SPIN_UP_TRIMMED_YEARS)) else years)


def record_for(setup):
    """The record of the economy after the hidden years on `setup`, from the disk cache when it holds it."""
    return solve_cache.cached_json(spin_up_cache_key(setup), lambda: spun_up(setup), cache_dir=SPIN_UP_CACHE_DIRECTORY)


def spun_up(setup):
    """The record after the hidden years, run on a fresh economy."""
    economy = economy_api.blank_economy(setup)
    economy_api.begin_spin_up(economy)
    spin_up(economy)
    return economy_api.export_record(economy, (PURSE_CURRENCY,))


def spin_up(economy):
    """Hidden years from the opening until prices and the interest rate settle; then the price level is rebased to one."""
    basket = economy_api.opening_quantities(economy)
    prices = economy_api.opening_prices_of(economy)
    watched = sorted(basket, key=lambda good: -basket[good] * prices.get(good, 0.0))[:SPIN_UP_WATCHED_GOODS]
    inputs = YearInputs(year=0, population_by_tile={},
                        yield_factor_by_producer=port_sites.crop_yields(economy), engine_orders={})
    first_stage = settle(economy, inputs, watched)
    economy_api.trim_workforce_to_expected_hours(economy)
    final_states = settle_trimmed(economy, inputs, watched)
    economy_api.trim_workforce_to_expected_hours(economy)   # the trade the settled years left idle does not carry its people into the game
    economy_api.finish_spin_up(economy)
    years = first_stage["years"] + spin_up_years()[1]
    economy_api.note_spin_up_result(economy, final_result(first_stage, final_states, years))


def settle(economy, inputs, watched):
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
        now = (outcome.basket_price_level, economy_api.interest_rate(economy) or 0.0,
               {good: outcome.prices.get(good, 0.0) for good in watched})
        if before is not None:
            gap = max(change_gap(now[0], before[0]) if before[0] > 0.0 else 0.0,
                      change_gap(now[1], before[1], SPIN_UP_RATE_FLOOR) if before[1] > 0.0 else 0.0,
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
        state = economy_api.spin_up_state(economy, outcome)
        state.update(price_level=outcome.basket_price_level, rate=economy_api.interest_rate(economy) or 0.0,
                     prices={good: outcome.prices.get(good, 0.0) for good in watched})
        states.append(state)
    return list(states)


def final_result(first_stage, final_states, years):
    """What the saved opening reports, apart from the stop rule: whether the state it opens in (after
    trimming) moved less than the tolerance a year, in every quantity spin_up_gap measures, over the last
    consecutive years. {"settled", "years" (all hidden years), "gap" (largest change; one when fewer than two
    years were measured), "gaps" (by quantity), "measured_years", "final" (the last year's state),
    "first_stage" (the stop rule's own result)}."""
    gaps = window_gaps(final_states)
    gap = 1.0 if gaps is None else max(gaps.values())
    return {"settled": gaps is not None and gap < SPIN_UP_TOLERANCE, "years": years, "gap": gap,
            "gaps": gaps or {}, "measured_years": len(final_states),
            "final": dict(final_states[-1]) if final_states else {}, "first_stage": dict(first_stage)}
