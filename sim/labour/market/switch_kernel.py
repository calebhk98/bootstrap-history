"""Workers re-weigh their trade against the others, for every area of the year (the kernels behind `switching.switch_trades`).

Per area, in sorted order: the incomes of its trades (income_kernel.py), then rounds of choices. A round works out each (source
trade, young or established) group's odds (`switching_kernel.plan_area`), the moves that follow (`collect_moves`), takes the
switchers out of their trades and into training (`take_moves`, `group_moves`, `enrol_groups`), and re-reads the income after
training of the trades that took trainees in. Areas do not read each other, so they run in turn on the tables. New cohorts go to
the book's pending table (cohort_book.py). Names enter the views in the order the Python rule made them: counters stamp them.
"""
from typing import NamedTuple

import numpy as np

from sim.compiled_tables.growth import NO_ROOM
from sim.jit import njit

from . import cohort_book as cohorts
from .exact_sums import exact_sum
from .income_kernel import expected_income, idle_share, income_at_graduation, vacant_hours
from .switching_kernel import collect_moves, enrol_groups, group_moves, plan_area, take_moves

DONE, NO_ROOM_FOR_COHORTS = 0, 1       # what `switch_all` answers


class SwitchRules(NamedTuple):
    """The switching rule's constants (switching.py declares them)."""
    consideration_floor: float     # share of a trade's workers who reconsider it in a year
    remaining_share: float         # share of a career still ahead of an established worker
    plan_tolerance: float          # years of subsistence a destination's income may move before odds are worked out again
    taste: float                   # years of subsistence per e-fold of choice odds
    negligible: float              # share of the workers weighing a switch under which a destination is not trained for
    retraining_share: float        # share of the training years a related trade takes
    rounds: int                    # rounds of choices a year
    apprentices_per_master: float  # trainees taught at once per practising worker


class Destinations(NamedTuple):
    """The trades one can switch to and what the year's setup says of every trade."""
    trade: np.ndarray              # trade number of each destination, ascending
    chances: np.ndarray            # [destination, band] chance of finishing the training
    years: np.ndarray              # training years of each destination
    in_play: np.ndarray            # per trade: the year lists it
    family: np.ndarray             # per trade: a number for its skill family (equal numbers, equal families)
    position: np.ndarray           # per trade: its place among the destinations, -1 if it is not one
    fallback_trade: int
    fallback_position: int         # the fallback trade's place among the destinations, -1 if it is not one
    seats: np.ndarray              # per grid row: school seats teaching the trade in the area
    school_bonus: np.ndarray       # per grid row: those seats' completion bonus


class Switched(NamedTuple):
    """What the rule reports, by grid row, and the sequence counter that orders new entries."""
    net: np.ndarray                # people who came to the trade less those who left it
    seen: np.ndarray               # the pair appears in the report
    order: np.ndarray              # when it first appeared, for the report's order
    counter: np.ndarray            # one entry: the last sequence number given (the state's, so new entries of its views are stamped in turn)


@njit
def _stamp(counter):
    counter[0] += 1
    return counter[0]


@njit
def _name_worker_pair(workers, counter, row):
    """The workers view gets the pair (`aptitude.bands_of`), the area having an entry already."""
    if not workers.present[row]:
        workers.present[row] = True
        workers.order[row] = _stamp(counter)


@njit
def _find_sources(workers, destinations, area, trade_count, sources):
    """The trades of the area with people (a trade the year lists, band totals above zero), by number; how many."""
    found = 0
    for trade in range(trade_count):
        row = area * trade_count + trade
        if workers.present[row] and destinations.in_play[trade] and exact_sum(workers.people[row], workers.people.shape[1]) > 0.0:
            sources[found] = trade
            found += 1
    return found


@njit
def _fill_group_inputs(rates, rules, results, caps, hours, workers, book, destinations, area, sources, count, scratch_caps, scratch_hours,
                       income, idle, vacancies, source_position, source_is_fallback, training_share):
    """The area's incomes, idle shares, vacancies and retraining shares by source and destination; returns the unskilled option."""
    trade_count = destinations.in_play.shape[0]
    for source in range(count):
        trade = sources[source]
        income[source] = expected_income(rates, results, caps, hours, workers.people, workers.present, area, trade, scratch_caps, scratch_hours)
        idle[source] = idle_share(results, area * trade_count + trade)
        source_position[source] = destinations.position[trade]
        source_is_fallback[source] = trade == destinations.fallback_trade
        for destination in range(destinations.trade.shape[0]):
            same = destinations.family[trade] == destinations.family[destinations.trade[destination]]
            training_share[source, destination] = rules.retraining_share if same else 1.0
    for destination in range(destinations.trade.shape[0]):
        row = area * trade_count + destinations.trade[destination]
        vacancies[destination] = results.cleared[row] and vacant_hours(results, row) > 0.0
    return expected_income(rates, results, caps, hours, workers.people, workers.present, area, destinations.fallback_trade, scratch_caps, scratch_hours)


@njit
def _add_direct_entry(workers, counter, area, trade_count, destinations, added):
    """People who entered a trade needing no training join its workers (the pair is made if it was not there)."""
    for destination in range(added.shape[0]):
        anything = False
        for band in range(added.shape[1]):
            if added[destination, band] != 0.0:
                anything = True
        if not anything:
            continue
        row = area * trade_count + destinations.trade[destination]
        _name_worker_pair(workers, counter, row)
        for band in range(added.shape[1]):
            workers.people[row, band] += added[destination, band]


@njit
def _enrol_cohorts(areas, markets, book, counter, area, trade_count, destinations, group_destination, kind, years, bonus, admitted):
    """Each group's admitted people join the destination's cohorts: a new cohort (kind 1) or the newest one (kind 2).
    Returns whether the pending table had room."""
    for group in range(group_destination.shape[0]):
        row = area * trade_count + destinations.trade[group_destination[group]]
        if kind[group] == 1:
            if not areas.trainees_named[area]:
                areas.trainees_named[area] = True
                areas.trainees_order[area] = _stamp(counter)
            if cohorts.cohorts_in(book, row) == 0:
                markets.cohort_order[row] = _stamp(counter)
            if cohorts.add_cohort(book, row, years[group], bonus[group], admitted[group]) == NO_ROOM:
                return False
        elif kind[group] == 2:
            cohorts.add_to_last_cohort(book, row, admitted[group])
    return True


@njit
def _record_net(switched, area, trade_count, destinations, moves_source, moves_destination, moved, sources, source_count):
    """`switching._carry_out`'s net change per trade: destinations first, then sources, added to the year's report in that order."""
    destination_count = destinations.trade.shape[0]
    net = np.zeros(trade_count)
    named = np.zeros(trade_count, np.bool_)
    order = np.zeros(trade_count, np.int64)
    taken = np.zeros(destination_count)
    taken_flag = np.zeros(destination_count, np.bool_)
    left = np.zeros(source_count)
    left_flag = np.zeros(source_count, np.bool_)
    for move in range(moves_source.shape[0]):
        taken[moves_destination[move]] += moved[move]
        taken_flag[moves_destination[move]] = True
        left[moves_source[move]] += moved[move]
        left_flag[moves_source[move]] = True
    seen = 0
    for destination in range(destination_count):
        if taken_flag[destination]:
            trade = destinations.trade[destination]
            net[trade] = 0.0 + 1.0 * taken[destination]
            named[trade] = True
            order[trade] = seen
            seen += 1
    for source in range(source_count):
        if left_flag[source]:
            trade = sources[source]
            net[trade] = (net[trade] if named[trade] else 0.0) + -1.0 * left[source]
            if not named[trade]:
                named[trade] = True
                order[trade] = seen
                seen += 1
    for position in range(seen):
        for trade in range(trade_count):
            if named[trade] and order[trade] == position:
                row = area * trade_count + trade
                if not switched.seen[row]:
                    switched.seen[row] = True
                    switched.order[row] = _stamp(switched.counter)
                switched.net[row] = switched.net[row] + net[trade]


@njit
def _school_and_cohort_inputs(book, destinations, area, trade_count, group_destination, seats, school_bonus, enrolled, last_years, last_bonus,
                              last_exists):
    """For the destinations the groups go to: school seats and bonus, people enrolled, and the newest cohort's years and bonus."""
    for group in range(group_destination.shape[0]):
        destination = group_destination[group]
        row = area * trade_count + destinations.trade[destination]
        seats[destination] = destinations.seats[row]
        school_bonus[destination] = destinations.school_bonus[row]
        enrolled[destination] = cohorts.enrolled(book, row)
        exists, years, bonus = cohorts.last_cohort(book, row)
        last_exists[destination], last_years[destination], last_bonus[destination] = exists, years, bonus


@njit
def carry_out(rules, workers, areas, markets, book, destinations, switched, area, sources, source_count, counts, found, moves_source,
              moves_destination, moves_share, moves_rows, stale):
    """`switching._carry_out`: take the switchers out of their trades and into training. Sources moving to one destination on one
    training length apply together and the destination's places are shared out between them (`enrol_groups`). Marks in `stale`
    the destinations that took trainees in; returns whether the pending table had room."""
    trade_count = destinations.in_play.shape[0]
    destination_count, band_count = destinations.trade.shape[0], counts.shape[1]
    have = counts.copy()
    taken = np.empty((found, band_count))
    take_moves(moves_source[:found], moves_rows[:found], have, taken)
    group_of, members, starts = np.empty(found, np.int64), np.empty(found, np.int64), np.zeros(found + 1, np.int64)
    group_count = group_moves(moves_destination[:found], moves_share[:found], group_of, members, starts)
    group_destination, group_share = np.empty(group_count, np.int64), np.empty(group_count)
    for group in range(group_count):
        group_destination[group] = moves_destination[members[starts[group]]]
        group_share[group] = moves_share[members[starts[group]]]
    source_of_destination = np.full(destination_count, -1, np.int64)
    for source in range(source_count):
        if destinations.position[sources[source]] >= 0:
            source_of_destination[destinations.position[sources[source]]] = source
    seats, school_bonus, enrolled = np.zeros(destination_count), np.zeros(destination_count), np.zeros(destination_count)
    last_years, last_bonus = np.zeros(destination_count), np.zeros(destination_count)
    last_exists = np.zeros(destination_count, np.bool_)
    _school_and_cohort_inputs(book, destinations, area, trade_count, group_destination, seats, school_bonus, enrolled, last_years, last_bonus,
                              last_exists)
    admitted, added = np.zeros((group_count, band_count)), np.zeros((destination_count, band_count))
    kind, years, bonus = np.zeros(group_count, np.int64), np.zeros(group_count), np.zeros(group_count)
    moved, changed = np.zeros(found), np.zeros(source_count, np.bool_)
    enrol_groups(starts[:group_count + 1], members, group_destination, group_share, taken, moves_source[:found], have, source_of_destination, added,
                 destinations.years, rules.apprentices_per_master, seats, school_bonus, enrolled, last_years, last_bonus, last_exists,
                 admitted, kind, years, bonus, moved, changed)
    for move in range(found):
        changed[moves_source[move]] = True
    for source in range(source_count):
        if changed[source]:
            workers.people[area * trade_count + sources[source]] = have[source]
    _add_direct_entry(workers, switched.counter, area, trade_count, destinations, added)
    ok = _enrol_cohorts(areas, markets, book, switched.counter, area, trade_count, destinations, group_destination, kind, years, bonus, admitted)
    _record_net(switched, area, trade_count, destinations, moves_source[:found], moves_destination[:found], moved, sources, source_count)
    for group in range(group_count):
        stale[group_destination[group]] = True
    return ok
