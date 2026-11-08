"""A trade with vacancies and no people in an area gets its first hands, over the tables (the kernels behind `formation.form_trades`):
migrants from areas that hold the trade, then bonded people bought where the area's civilisation allows it (Complaints 644, 648).

Markets are visited in (area, trade) order and the people they take are taken from the state as it stands, so a kernel runs the
whole step. What happened is returned as events (migrations and bonded lots) for the caller to turn into the report. Sums that the
Python added with `sum` use `exact_sums.python_sum`."""
import math
from typing import NamedTuple

import numpy as np

from sim.compiled_tables.growth import NO_ROOM
from sim.jit import njit

from .exact_sums import python_sum
from .income_kernel import YearRates

DONE, OUT_OF_ROOM = 0, 1
MIGRATION, BONDED = 0, 1
LOT_FIELDS = 6          # destination area, origin area, trade, people, ask, carriage (columns of the lots array)
EVENT_FIELDS = 4        # area, trade, kind, people


class FormationWorld(NamedTuple):
    """What the step reads about the year besides the state and the results."""
    floor_per_hour: np.ndarray       # per area: the wage floor an hour; NaN: none stated
    annuity: float                   # present value of one unit a year over a career
    premium: np.ndarray              # per trade: wage multiple its training years earn
    bondage_allowed: np.ndarray      # per area: bonded people may be bought there
    leads_to: np.ndarray             # [origin, area]: a route runs from origin to area
    carriage: np.ndarray             # [origin, area]: cheapest cost of carrying a person; NaN where there is no way
    bid_first: np.ndarray            # per grid row: first entry of its employers' bid hours
    bid_count: np.ndarray            # per grid row: how many employers bid
    bid_employer: np.ndarray         # per entry: the employer, entries of a market in order of employer name
    bid_hours: np.ndarray            # per entry: hours that employer bid for in the market


class HiredHours(NamedTuple):
    """The hours each employer was hired for at the clearing, per market (`Results.hired_first` and `hired_count` index them)."""
    employer: np.ndarray
    hours: np.ndarray


@njit
def add_up_bids(row, employer, hours, first, count, entry_employer, entry_hours):
    """Add the bids of one employer in one market: `row`, `employer` and `hours` come sorted by market then employer name, the
    bids of an employer in the order given. Fills each market's `first` entry and `count`; returns the number of entries."""
    entries = 0
    for bid in range(row.shape[0]):
        if bid == 0 or row[bid] != row[bid - 1]:
            first[row[bid]] = entries
        if bid > 0 and row[bid] == row[bid - 1] and employer[bid] == employer[bid - 1]:
            entry_hours[entries - 1] += hours[bid]
        else:
            entry_employer[entries] = employer[bid]
            entry_hours[entries] = 0.0 + hours[bid]
            count[row[bid]] += 1
            entries += 1
    return entries


@njit
def worth_in(rates, world, area, trade, trade_wage):
    """`formation_bonded.worth_in`: present value of a trained person's hours in the area over a career; NaN when neither the
    trade's wage nor the area's wage floor is known there."""
    floor = world.floor_per_hour[area]
    no_floor = math.isnan(floor) or floor <= 0.0
    no_wage = math.isnan(trade_wage) or trade_wage <= 0.0
    if no_floor and no_wage:
        return np.nan
    if math.isnan(floor):
        floor = 0.0
    premium_wage = max(0.0, floor) * world.premium[trade]
    wage = max(premium_wage, trade_wage) if not no_wage else premium_wage
    return max(0.0, wage) * max(0.0, rates.hours) * world.annuity


@njit
def practised_wage(results, row):
    """The wage the trade pays where it was practised this year; NaN where no hour was hired."""
    if results.cleared[row] and results.hours_hired[row] > 0.0:
        return results.wage[row]
    return np.nan


@njit
def heading_wage(results, row):
    """`LabourClearing.heading_wage`."""
    return results.wage[row] if math.isnan(results.target_wage[row]) else results.target_wage[row]


@njit
def held_people(workers, book_first, book_count, cohort_people, row):
    """`formation._held`: the people of the trade in the area, working or learning (sum of band sums)."""
    held = 0.0
    if workers.present[row]:
        held = python_sum(workers.people[row], workers.people.shape[1])
    for cohort in range(book_first[row], book_first[row] + book_count[row]):
        held += python_sum(cohort_people[cohort], cohort_people.shape[1])
    return held


@njit
def take_from(workers, row, people, taken):
    """`formation._take_from`: remove `people` of the trade from the pair in proportion to its bands; the bands taken."""
    total = python_sum(workers.people[row], workers.people.shape[1])
    share = min(1.0, people / total) if total > 0.0 else 0.0
    for band in range(workers.people.shape[1]):
        taken[band] = workers.people[row, band] * share
        workers.people[row, band] -= taken[band]


@njit
def _name_pair(workers, areas, counter, area, row):
    if not areas.workers_named[area]:
        areas.workers_named[area] = True
        counter[0] += 1
        areas.workers_order[area] = counter[0]
    if not workers.present[row]:
        workers.present[row] = True
        counter[0] += 1
        workers.order[row] = counter[0]
        workers.length[row] = workers.people.shape[1]


@njit
def spare_origins(rates, results, workers, world, area, trade, trade_count, spare, areas_count):
    """`formation.spare_people` for every origin with a route to the area that holds the trade; zero for the others (an origin with
    nothing to spare takes nothing, so it need not be told apart)."""
    for origin in range(areas_count):
        spare[origin] = 0.0
        if origin == area or not world.leads_to[origin, area]:
            continue
        row = origin * trade_count + trade
        held = python_sum(workers.people[row], workers.people.shape[1]) if workers.present[row] else 0.0
        if held <= 0.0:
            continue
        wanted = results.hours_wanted[row] if results.cleared[row] else 0.0
        spare[origin] = max(0.0, held - max(0.0, wanted) / max(rates.hours, 1e-12))


@njit
def migration_takes(wanted, spare, takes_origin, takes_people):
    """`formation.migration_takes`: (origin, people) drawn from the origins with most spare hands first (ties by name) until
    `wanted` is met, over the origins with something to spare. Returns how many takes there are."""
    remaining = wanted
    count = 0
    used = np.zeros(spare.shape[0], np.bool_)
    for _pass in range(spare.shape[0]):
        best = -1
        for origin in range(spare.shape[0]):
            if spare[origin] <= 0.0 or used[origin]:
                continue
            if best < 0 or spare[origin] > spare[best]:
                best = origin
        if best < 0:
            break
        used[best] = True
        take = min(remaining, max(0.0, spare[best]))
        if take > 0.0:
            takes_origin[count], takes_people[count] = best, take
            count += 1
            remaining -= take
    return count
