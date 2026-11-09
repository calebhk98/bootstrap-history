"""Block reads of the labour core's state for the economy's year (docs/architecture/COMPILED_YEAR.md, stage 4).

Each function answers for many areas, trades or markets in one kernel call (state_read_kernels.py) over the state's tables, where the
dict views (state_fields.py) answered one value per call. They return the figures the views gave, in the order the views listed them.
Areas and trades are named; a name the state does not number reads as nothing."""
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy

from . import state_read_kernels as kernels


def numbers_of(sorted_names: Sequence[str], names: Iterable[str]) -> numpy.ndarray:
    """The place of each name among `sorted_names` (the state's numbering), -1 for a name not among them."""
    queries = numpy.asarray(names if isinstance(names, numpy.ndarray) else list(names), dtype=str)
    if not len(queries) or not len(sorted_names):
        return numpy.full(len(queries), -1, dtype=numpy.int64)
    known = numpy.asarray(sorted_names, dtype=str)
    places = numpy.minimum(numpy.searchsorted(known, queries), len(known) - 1)
    return numpy.where(known[places] == queries, places, -1).astype(numpy.int64)


def area_numbers(state, areas: Iterable[str]) -> numpy.ndarray:
    """The state's number of each area, -1 for an area it does not number."""
    return numbers_of(state.ids.areas.names, areas)


def grid_rows_of(state, areas: Iterable[str], trades: Iterable[str]) -> numpy.ndarray:
    """The grid row of each (area, trade) pair given as two lists of equal length; -1 where the state numbers neither."""
    area_found, trade_found = area_numbers(state, areas), numbers_of(state.ids.trades.names, trades)
    return numpy.where((area_found >= 0) & (trade_found >= 0), area_found * len(state.ids.trades) + trade_found, -1)


def hours_cleared_at(state, rows: numpy.ndarray) -> numpy.ndarray:
    """Hours the last clearing hired in each market (grid rows given), all employers: what `hired_hours[area][trade]` summed to."""
    markets = state.market_table
    return kernels.hired_hours_at(numpy.asarray(rows, dtype=numpy.int64), markets.hired_first, markets.hired_count, state.hired_table.hours)


def people_at(state, rows: numpy.ndarray) -> numpy.ndarray:
    """Working people of each pair (grid rows given): what `fsum(workers[area][trade])` gave, zero for a pair with no entry."""
    table = state.workers_table
    return kernels.people_at(numpy.asarray(rows, dtype=numpy.int64), table.present, table.people, table.length)


def people_by_trade_over(state, areas: Iterable[str]) -> Dict[str, float]:
    """Working people by trade over the areas, added area by area in the order given (a trade with an entry in one of them has a
    figure, even zero), trades in name order. Trainees are not counted."""
    table = state.workers_table
    totals, seen = kernels.trade_people_over_areas(area_numbers(state, areas), len(state.ids.trades), table.present, table.people, table.length)
    names = state.ids.trades.names
    return {names[trade]: float(totals[trade]) for trade in numpy.flatnonzero(seen).tolist()}


def people_by_trade_in_each_area(state, areas: Iterable[str]) -> Tuple[numpy.ndarray, numpy.ndarray]:
    """Working people of every trade in each area given, one kernel call: (people, seen), each of shape (areas, trades) with the
    trades in name order. A row is what `people_by_trade_over(state, [area])` holds, as a column per trade; a trade with an entry
    in the area is `seen`, even at zero. Trainees are not counted."""
    table = state.workers_table
    return kernels.trade_people_by_area(area_numbers(state, areas), len(state.ids.trades), table.present, table.people, table.length)


def working_people_in_areas(state, areas: Iterable[str]) -> numpy.ndarray:
    """For each area, `fsum` of its trades' people (each `fsum` of the bands); zero for an area the state does not number."""
    table = state.workers_table
    return kernels.working_people_in_areas(area_numbers(state, areas), len(state.ids.trades), table.present, table.people, table.length)


def _pairs_in_view_order(state, areas: numpy.ndarray, present: numpy.ndarray, order: numpy.ndarray, named: numpy.ndarray):
    """The grid rows with an entry in each listed area (numbers; areas the view does not name have none): (rows, place of the area in
    the list), areas in the order given and, inside an area, in the order the view lists its trades."""
    trades = len(state.ids.trades)
    grid = (areas[:, None] * trades + numpy.arange(trades)[None, :]).ravel()
    place = numpy.repeat(numpy.arange(len(areas)), trades)
    keep = present[grid] & named[numpy.repeat(areas, trades)]
    grid, place = grid[keep], place[keep]
    ordered = numpy.lexsort((order[grid], place))
    return grid[ordered], place[ordered]


def _starts(place: numpy.ndarray, count: int) -> numpy.ndarray:
    return numpy.searchsorted(place, numpy.arange(count + 1)).astype(numpy.int64)


def _cohort_rows(state, areas: numpy.ndarray) -> Tuple[numpy.ndarray, numpy.ndarray]:
    """The trainee rows of each listed area in the order the trainees view lists them: (rows, place of the area in the list)."""
    markets = state.market_table
    pair_rows, pair_place = _pairs_in_view_order(state, areas, markets.cohort_count > 0, markets.cohort_order, state.areas_table.trainees_named)
    counts = markets.cohort_count[pair_rows]
    offsets = numpy.cumsum(counts) - counts
    rows = numpy.repeat(markets.cohort_first[pair_rows] - offsets, counts) + numpy.arange(int(counts.sum()))
    return rows.astype(numpy.int64), numpy.repeat(pair_place, counts)


def people_in_areas(state, areas: Sequence[str], include_trainees: bool = True) -> numpy.ndarray:
    """Everyone counted in each area, working or learning: the trades in the order the workers view lists them, then the cohorts in the
    order the trainees view lists them, each band list summed by `sum`. Zero for an area the state does not number."""
    found = area_numbers(state, areas)
    count = len(found)
    if not len(state.ids.trades):
        return numpy.zeros(count)
    known = numpy.maximum(found, 0)
    workers, trainees = state.workers_table, state.trainee_table
    worker_rows, worker_place = _pairs_in_view_order(state, known, workers.present, workers.order, state.areas_table.workers_named)
    keep = found[worker_place] >= 0
    worker_rows, worker_place = worker_rows[keep], worker_place[keep]
    cohort_rows, cohort_place = numpy.zeros(0, dtype=numpy.int64), numpy.zeros(0, dtype=numpy.int64)
    if include_trainees:
        cohort_rows, cohort_place = _cohort_rows(state, known)
        keep = found[cohort_place] >= 0
        cohort_rows, cohort_place = cohort_rows[keep], cohort_place[keep]
    return kernels.ordered_people_totals(worker_rows, _starts(worker_place, count), workers.people, workers.length,
                                         cohort_rows, _starts(cohort_place, count), trainees.people, trainees.length)


def scale_people_in_area(state, area: str, factor: float) -> None:
    """Multiply every worker and trainee of the area by `factor`, band by band."""
    number = state.ids.areas.find(area)
    if number is None or not len(state.ids.trades):
        return
    trades = len(state.ids.trades)
    first, stop = number * trades, (number + 1) * trades
    workers, markets = state.workers_table, state.market_table
    kernels.scale_pairs(first, stop, factor, workers.present, workers.people, workers.length)
    first_cohort = int(markets.cohort_first[first])
    kernels.scale_cohorts(first_cohort, first_cohort + int(markets.cohort_count[first:stop].sum()), factor, state.trainee_table.people,
                          state.trainee_table.length)


def scale_people_in_areas(state, areas: Sequence[str], factors: numpy.ndarray) -> None:
    """`scale_people_in_area` for each area by its own factor (an area the state does not number is left as it is)."""
    if not len(state.ids.trades):
        return
    workers, markets = state.workers_table, state.market_table
    kernels.scale_areas(area_numbers(state, areas), numpy.asarray(factors, dtype=numpy.float64), len(state.ids.trades), workers.present,
                        workers.people, workers.length, markets.cohort_first, markets.cohort_count, state.trainee_table.people,
                        state.trainee_table.length)


def wages_in_view_order(state, above: float) -> Tuple[List[str], List[str], numpy.ndarray]:
    """The wages greater than `above`, as (area names, trade names, wages) in the order `state.wages` lists them: areas in the order
    they were named, and inside an area the trades in the order they got their wages."""
    markets, areas = state.market_table, state.areas_table
    trades = len(state.ids.trades)
    rows = numpy.flatnonzero(markets.wage > above)
    rows = rows[areas.wages_named[rows // trades]]
    rows = rows[numpy.lexsort((markets.wage_order[rows], areas.wages_order[rows // trades]))]
    area_names, trade_names = numpy.asarray(state.ids.areas.names), numpy.asarray(state.ids.trades.names)
    return area_names[rows // trades].tolist(), trade_names[rows % trades].tolist(), markets.wage[rows]


def people_weighted_wage_by_area(state) -> Dict[str, float]:
    """For each area with a wage, the mean of its trades' wages weighted by the people working each (plain where nobody works any),
    areas in name order."""
    workers, markets = state.workers_table, state.market_table
    means, exists = kernels.people_weighted_wage_by_area(len(state.ids.trades), state.areas_table.wages_named, markets.wage,
                                                         workers.present, workers.people, workers.length)
    names = state.ids.areas.names
    return {names[area]: float(means[area]) for area in numpy.flatnonzero(exists).tolist()}


def wage_means_by_group(group_ends, kept, wage, hours, people) -> Tuple[numpy.ndarray, numpy.ndarray]:
    """(mean, exists) per group of consecutive places: the wage weighted by hours, else by people, else plain; see the kernel."""
    return kernels.wage_means_by_group(numpy.asarray(group_ends, dtype=numpy.int64), kept, wage, hours, people)
