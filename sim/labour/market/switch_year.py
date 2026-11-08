"""The year's switching of trades over every area (`switching.switch_trades` runs it): per area, its incomes and then the rounds."""
import math

import numpy as np

from sim.jit import njit

from .income_kernel import income_at_graduation
from .switch_kernel import DONE, NO_ROOM_FOR_COHORTS, _find_sources, _fill_group_inputs, carry_out
from .switching_kernel import collect_moves, plan_area


@njit
def _refresh_later_income(rates, results, caps, hours, workers, book, destinations, area, stale, later, scratch_caps, scratch_hours):
    """The income after training of the destinations marked stale, worked out afresh."""
    trade_count = destinations.in_play.shape[0]
    for destination in range(destinations.trade.shape[0]):
        if stale[destination]:
            later[destination] = income_at_graduation(rates, results, caps, hours, workers.people, workers.present, book, area,
                                                      destinations.trade[destination], destinations.chances[destination], scratch_caps,
                                                      scratch_hours)


@njit
def switch_area(rates, rules, results, caps, hours, workers, areas, markets, book, destinations, switched, area, sources, source_count,
                scratch_caps, scratch_hours):
    """One area's rounds of switching (`switching.switch_trades` for the area). Returns DONE or NO_ROOM_FOR_COHORTS."""
    trade_count = destinations.in_play.shape[0]
    destination_count, band_count = destinations.trade.shape[0], workers.people.shape[1]
    income, idle = np.zeros(source_count), np.zeros(source_count)
    vacancies = np.zeros(destination_count, np.bool_)
    source_position = np.zeros(source_count, np.int64)
    source_is_fallback = np.zeros(source_count, np.bool_)
    training_share = np.zeros((source_count, destination_count))
    baseline = _fill_group_inputs(rates, rules, results, caps, hours, workers, book, destinations, area, sources, source_count, scratch_caps,
                                  scratch_hours, income, idle, vacancies, source_position, source_is_fallback, training_share)
    valid = np.zeros((source_count, 2), np.bool_)
    then = np.zeros((source_count, 2, destination_count))
    targets = np.zeros((source_count, 2, destination_count), np.bool_)
    shares = np.zeros((source_count, 2, band_count, destination_count))
    moving = np.zeros((source_count, 2, band_count), np.bool_)
    active = np.zeros((source_count, 2), np.bool_)
    considering = np.zeros((source_count, 2))
    stale = np.ones(destination_count, np.bool_)
    later = np.zeros(destination_count)
    possible = source_count * 2 * destination_count
    moves_source, moves_destination = np.empty(possible, np.int64), np.empty(possible, np.int64)
    moves_share, moves_rows = np.empty(possible), np.empty((possible, band_count))
    counts = np.empty((source_count, band_count))
    for _round in range(rules.rounds):
        _refresh_later_income(rates, results, caps, hours, workers, book, destinations, area, stale, later, scratch_caps, scratch_hours)
        stale[:] = False
        for source in range(source_count):
            counts[source] = workers.people[area * trade_count + sources[source]]
        plan_area(counts, income, idle, baseline, later, vacancies, destinations.chances, destinations.years, training_share, source_position,
                  source_is_fallback, destinations.fallback_position, rates.subsistence[area], rates.discount_rate, rates.career_years,
                  rules.consideration_floor, rules.remaining_share, rules.plan_tolerance, rules.taste, rules.negligible, valid, then, targets,
                  shares, moving, active, considering)
        found = collect_moves(counts, considering, active, moving, shares, training_share, rules.rounds, moves_source, moves_destination,
                              moves_share, moves_rows)
        if found > 0 and not carry_out(rules, workers, areas, markets, book, destinations, switched, area, sources, source_count, counts, found,
                                       moves_source, moves_destination, moves_share, moves_rows, stale):
            return NO_ROOM_FOR_COHORTS
    return DONE


@njit
def switch_all(rates, rules, results, caps, hours, workers, areas, markets, book, destinations, switched):
    """Every area that holds workers and states a subsistence, in sorted order. Returns DONE or NO_ROOM_FOR_COHORTS."""
    trade_count = destinations.in_play.shape[0]
    longest = 1
    for row in range(results.demand_count.shape[0]):
        if results.demand_count[row] > longest:
            longest = results.demand_count[row]
    scratch_caps, scratch_hours = np.empty(longest + 1), np.empty(longest + 1)
    sources = np.empty(trade_count, np.int64)
    for area in range(areas.workers_named.shape[0]):
        if not areas.workers_named[area]:
            continue
        if math.isnan(rates.subsistence[area]) or rates.subsistence[area] <= 0.0:
            continue
        source_count = _find_sources(workers, destinations, area, trade_count, sources)
        if source_count == 0:
            continue
        if switch_area(rates, rules, results, caps, hours, workers, areas, markets, book, destinations, switched, area, sources, source_count,
                       scratch_caps, scratch_hours) != DONE:
            return NO_ROOM_FOR_COHORTS
    return DONE
