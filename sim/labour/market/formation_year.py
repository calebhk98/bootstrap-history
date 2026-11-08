"""The year's formation of empty trades over every market (`formation.form_trades` runs it): where employers want hours of a trade
that no one in the area works or learns, the first people come from migrants (areas that hold the trade, up to their spare hands),
then bonded people are bought where the civilisation allows it; any other market with vacancies may buy bonded people the same way."""
import numpy as np

from sim.jit import njit

from .formation_buy import add_event, buy_bonded
from .formation_kernel import DONE, MIGRATION, OUT_OF_ROOM, _name_pair, held_people, migration_takes, spare_origins, take_from
from .exact_sums import python_sum
from .income_kernel import vacant_hours


@njit
def _find_empty_trades(rates, results, workers, cohort_first, cohort_count, cohort_people, empty, wanted):
    """Markets where employers want hands and no one of the trade works or trains in the area."""
    for row in range(results.cleared.shape[0]):
        empty[row] = False
        if not results.cleared[row]:
            continue
        wanted[row] = vacant_hours(results, row) / rates.hours
        empty[row] = wanted[row] > 0.0 and held_people(workers, cohort_first, cohort_count, cohort_people, row) <= 0.0


@njit
def _take_migrants(rates, world, results, workers, areas, counter, out, area, trade, trade_count, wanted):
    """Fill the market from origins that can spare hands; returns whether the outputs had room and the people still wanted."""
    area_count = world.leads_to.shape[0]
    spare = np.zeros(area_count)
    spare_origins(rates, results, workers, world, area, trade, trade_count, spare, area_count)
    takes_origin, takes_people = np.empty(area_count, np.int64), np.empty(area_count)
    takes = migration_takes(wanted, spare, takes_origin, takes_people)
    taken = np.empty(workers.people.shape[1])
    row = area * trade_count + trade
    for take in range(takes):
        take_from(workers, takes_origin[take] * trade_count + trade, takes_people[take], taken)
        _name_pair(workers, areas, counter, area, row)
        for band in range(taken.shape[0]):
            workers.people[row, band] += taken[band]
        if not add_event(out, area, trade, MIGRATION, python_sum(taken, taken.shape[0])):
            return False, wanted
    return True, wanted - python_sum(takes_people, takes)


@njit
def form_all(rates, world, results, workers, areas, markets, hired, cohort_people, pool, unassigned, counter, out):
    """Both passes over the markets in (area, trade) order. Returns DONE, or OUT_OF_ROOM when `out` filled up (the caller makes more
    room and runs the step again from a copy of the state it took before)."""
    trade_count = world.premium.shape[0]
    rows = results.cleared.shape[0]
    empty, wanted = np.zeros(rows, np.bool_), np.zeros(rows)
    _find_empty_trades(rates, results, workers, markets.cohort_first, markets.cohort_count, cohort_people, empty, wanted)
    for row in range(rows):
        if not empty[row]:
            continue
        area, trade = row // trade_count, row % trade_count
        room, still = _take_migrants(rates, world, results, workers, areas, counter, out, area, trade, trade_count, wanted[row])
        if not room:
            return OUT_OF_ROOM
        if not buy_bonded(rates, world, results, workers, areas, hired, pool, unassigned, counter, out, area, trade, trade_count, still):
            return OUT_OF_ROOM
    on_offer = np.zeros(trade_count, np.bool_)
    for trade in range(trade_count):
        on_offer[trade] = pool[:, trade].max() > 0.0 if pool.shape[0] else False
    for row in range(rows):
        if empty[row] or not results.cleared[row] or not vacant_hours(results, row) > 0.0:
            continue
        area, trade = row // trade_count, row % trade_count
        if on_offer[trade] and world.bondage_allowed[area]:
            if not buy_bonded(rates, world, results, workers, areas, hired, pool, unassigned, counter, out, area, trade, trade_count,
                              vacant_hours(results, row) / rates.hours):
                return OUT_OF_ROOM
    return DONE
