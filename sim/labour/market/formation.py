"""A trade with vacancies and no people in an area gets its first hands (Complaint 644).

Run after the year's switching and migration. For each (area, trade) where employers want hours and no
one of the trade works or trains, the first people come from the routes that need no teacher: migrants from
areas that hold the trade (up to their spare hands), then bonded people bought where the area's
civilisation allows it, at the owners' ask and the buyers' bid (formation_bonded.py). Any trade still short of hands after that may buy bonded people the same way. Conversion
needs a teacher and a payer, so the caller's own verbs (training schools) carry it out. Any employer's
vacancy counts, not one actor's.
"""
from typing import List

import numpy as np

from . import bid_book, formation_buy, formation_kernel, formation_year
from .bonded_worth import BondedLot
from .formation_buy import Outputs
from .formation_kernel import FormationWorld
from .market_state import MarketState
from .premium import annuity_factor, training_premium
from .records import YearInputs, YearReport
from .results_grid import grid_of
from .year_carriage import dense_carriage
from .year_rates import rates_of

def spare_people(workers: float, hours_wanted: float, hours_per_worker_year: float) -> float:
    """People of a trade an area could release: its workers less those its employers' bids still need."""
    return max(0.0, workers - max(0.0, hours_wanted) / max(hours_per_worker_year, 1e-12))


ROOM_AT_FIRST = 64      # events, lots, purchases and payers the step has room for before it is run again with more


def _bid_hours_by_employer(state: MarketState, inputs: YearInputs):
    """Per grid row, the hours each employer bid for there, employers in name order: (first entry, entries, employer, hours).
    An employer's bids in a market add in the order they were given."""
    ids = state.ids
    bids = bid_book.numbered(state, inputs.bids)
    trade_count = len(ids.trades)
    rows = len(ids.areas) * trade_count
    use = (bids.area >= 0) & (bids.trade >= 0) & (bids.hours > 0.0)
    row, employer, hours = (bids.area * trade_count + bids.trade)[use], bids.employer[use], bids.hours[use]
    order = np.lexsort((ids.employers.rank[employer], row))
    row, employer, hours = row[order], employer[order], hours[order]
    first, count = np.zeros(rows, np.int64), np.zeros(rows, np.int64)
    entry_employer, entry_hours = np.zeros(len(row), np.int64), np.zeros(len(row))
    entries = formation_kernel.add_up_bids(row, employer, hours, first, count, entry_employer, entry_hours)
    return first, count, entry_employer[:entries], entry_hours[:entries]


def _world(state: MarketState, inputs: YearInputs) -> FormationWorld:
    ids = state.ids
    area_count, trade_count = len(ids.areas), len(ids.trades)
    floor = np.full(area_count, np.nan)
    for area, stated in inputs.ask_floor_per_worker_year.items():
        floor[ids.areas.number(area)] = stated / max(inputs.hours_per_worker_year, 1e-12)
    premium = np.array([training_premium(inputs.trades[name].training_years if name in inputs.trades else 0.0, inputs.discount_rate,
                                         inputs.career_years) for name in ids.trades.names])
    allowed = np.zeros(area_count, np.bool_)
    for area in inputs.bondage_allowed:
        allowed[ids.areas.number(area)] = True
    leads_to = np.zeros((area_count, area_count), np.bool_)
    for origin, ways in inputs.routes.items():
        for route in ways:
            leads_to[ids.areas.number(origin), ids.areas.number(route.destination)] = True
    carriage = dense_carriage(state, inputs) if allowed.any() else np.full((area_count, area_count), np.nan)
    first, count, employer, hours = _bid_hours_by_employer(state, inputs)
    return FormationWorld(floor, annuity_factor(inputs.discount_rate, inputs.career_years), premium, allowed, leads_to, carriage, first, count,
                          employer, hours)


def _outputs(room: int) -> Outputs:
    return Outputs(np.zeros(4, np.int64), np.zeros(room, np.int64), np.zeros(room, np.int64), np.zeros(room, np.int64), np.zeros(room),
                   np.zeros(room, np.int64), np.zeros(room), np.zeros(room), np.zeros(room), np.zeros(room, np.int64), np.zeros(room, np.int64),
                   np.zeros(room, np.int64), np.zeros(room, np.int64), np.zeros(room, np.int64), np.zeros(room, np.int64), np.zeros(room))


def _lots(state: MarketState, out: Outputs) -> List[BondedLot]:
    """The lots the step bought, in the order they were bought, with the employers that paid for each purchase."""
    ids = state.ids
    lots = []
    purchases = out.purchase_first[:out.counts[2]].tolist(), out.purchase_payers[:out.counts[2]].tolist()
    for lot in range(int(out.counts[1])):
        purchase = int(out.lot_purchase[lot])
        first, payers = purchases[0][purchase], purchases[1][purchase]
        paid = tuple((ids.employers.name(int(out.payer_employer[slot])), float(out.payer_share[slot])) for slot in range(first, first + payers))
        lots.append(BondedLot(ids.areas.names[out.purchase_area[purchase]], ids.trades.names[out.purchase_trade[purchase]],
                              ids.areas.names[out.lot_origin[lot]], float(out.lot_people[lot]), float(out.lot_ask[lot]),
                              float(out.lot_carriage[lot]), paid))
    return lots


def form_trades(state: MarketState, inputs: YearInputs, clearings, report: YearReport) -> None:
    """Fill empty trades' vacancies by migration and bonded purchase; record them in `report.formed` and `report.bonded_lots`
    (`formation_year.form_all`). `clearings` is the year's `Clearings`, a sequence of `LabourClearing`s or a mapping of them."""
    if inputs.hours_per_worker_year <= 0.0:
        return
    ids = state.ids
    state.admit([area for area in inputs.routes] + list(inputs.bondage_allowed) + list(inputs.bonded_for_sale) + list(inputs.ask_floor_per_worker_year)
                + [route.destination for ways in inputs.routes.values() for route in ways],
                list(inputs.trades) + [trade for by_trade in inputs.bonded_for_sale.values() for trade in by_trade])
    grid = grid_of(state, clearings.values() if isinstance(clearings, dict) else clearings)
    if not grid.results.cleared.any():
        return
    ids.employers.admit(inputs.outlay_room)
    world, rates = _world(state, inputs), rates_of(state, inputs)
    pool = np.zeros((len(ids.areas), len(ids.trades)))
    for origin, by_trade in inputs.bonded_for_sale.items():
        for trade, people in by_trade.items():
            pool[ids.areas.number(origin), ids.trades.number(trade)] = people
    unassigned = np.zeros(len(ids.employers))
    for employer, room in inputs.outlay_room.items():
        unassigned[ids.employers.table.number(employer)] = room
    saved = (state.workers_table.people.copy(), state.workers_table.present.copy(), state.workers_table.order.copy(),
             state.areas_table.workers_named.copy(), state.areas_table.workers_order.copy(), pool.copy(), unassigned.copy(), state._order)
    room = ROOM_AT_FIRST
    while True:
        out, counter = _outputs(room), np.array([state._order], np.int64)
        held = formation_kernel.HiredHours(grid.hired_employer, grid.hired_hours)
        status = formation_year.form_all(rates, world, grid.results, state.workers_table, state.areas_table, state.market_table, held,
                                         state.trainee_table.people, pool, unassigned, counter, out)
        if status == formation_kernel.DONE:
            break
        for table, kept in zip((state.workers_table.people, state.workers_table.present, state.workers_table.order, state.areas_table.workers_named,
                                state.areas_table.workers_order, pool, unassigned), saved):
            table[...] = kept
        room *= 4
    state._order = int(counter[0])
    for event in range(int(out.counts[0])):
        area, trade = ids.areas.names[out.event_area[event]], ids.trades.names[out.event_trade[event]]
        by_route = report.formed.setdefault(area, {}).setdefault(trade, {})
        kind = "migration" if out.event_kind[event] == formation_kernel.MIGRATION else "bonded"
        by_route[kind] = by_route.get(kind, 0.0) + float(out.event_people[event])
    report.bonded_lots.extend(_lots(state, out))
