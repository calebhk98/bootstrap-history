"""Buying bonded people for the vacancies of a trade (Complaints 644 and 648), over the tables (the kernels behind
`formation_bonded.buy`): by the owners' ask and the buyers' bid, within the room the employers' plans leave (bonded_room.py).

What a purchase did is appended to the step's outputs (`Outputs`): an event for the report, the lots bought, who paid and in what
share. A kernel that finds an output array full returns `False` and the caller runs the step again with more room."""
import math
from typing import NamedTuple

import numpy as np

from sim.jit import njit

from .exact_sums import python_sum
from .formation_kernel import BONDED, _name_pair, heading_wage, practised_wage, worth_in

SMALLEST_LOT = 1e-12      # people: a purchase under this is not made


class Outputs(NamedTuple):
    """Everything the step reports, as arrays with room for `event_area.shape[0]` events, lots, purchases and payers."""
    counts: np.ndarray            # used so far: events, lots, purchases, payers
    event_area: np.ndarray
    event_trade: np.ndarray
    event_kind: np.ndarray        # MIGRATION or BONDED
    event_people: np.ndarray
    lot_origin: np.ndarray        # area the people were bought in
    lot_people: np.ndarray
    lot_ask: np.ndarray           # the owners' ask a person
    lot_carriage: np.ndarray      # carriage a person
    lot_purchase: np.ndarray      # the purchase the lot belongs to
    purchase_area: np.ndarray     # the area the purchase was for
    purchase_trade: np.ndarray
    purchase_first: np.ndarray    # its first payer
    purchase_payers: np.ndarray   # how many payers
    payer_employer: np.ndarray
    payer_share: np.ndarray       # share of the price the employer pays


@njit
def add_event(out, area, trade, kind, people):
    """Append an event; False when there is no room."""
    slot = out.counts[0]
    if slot >= out.event_area.shape[0]:
        return False
    out.event_area[slot], out.event_trade[slot], out.event_kind[slot], out.event_people[slot] = area, trade, kind, people
    out.counts[0] += 1
    return True


@njit
def _hired_by(results, hired, row, employer):
    """Hours the employer was hired for in the market at the clearing (zero if none)."""
    for entry in range(results.hired_first[row], results.hired_first[row] + results.hired_count[row]):
        if hired.employer[entry] == employer:
            return hired.hours[entry]
    return 0.0


@njit
def _find_buyers(world, results, hired, unassigned, row, buyer_employer, buyer_vacant, buyer_line, buyer_free):
    """`bonded_room.buyers_in`: the employers with a vacancy in the market and some room to pay for a person, in employer-name
    order; how many."""
    count = 0
    heading = heading_wage(results, row)
    for entry in range(world.bid_first[row], world.bid_first[row] + world.bid_count[row]):
        employer = world.bid_employer[entry]
        vacant = max(0.0, world.bid_hours[entry] - _hired_by(results, hired, row, employer))
        line = vacant * max(0.0, heading)
        free = max(0.0, unassigned[employer])
        if vacant > 0.0 and line + free > 0.0:
            buyer_employer[count], buyer_vacant[count], buyer_line[count], buyer_free[count] = employer, vacant, line, free
            count += 1
    return count


@njit
def _buy_lots(rates, world, results, pool, area, trade, trade_count, wanted, bid_worth, lot_origin, lot_people, lot_ask, lot_carriage):
    """`bonded_worth.buy_lots`: lots for `wanted` people, cheapest landed price first, none dearer than `bid_worth`, out of the
    people for sale (`pool`, which it leaves as it was: the caller draws down what the lots finally keep). Returns how many lots."""
    area_count = pool.shape[0]
    left = pool[:, trade].copy()
    landed = np.full(area_count, np.nan)
    asks = np.full(area_count, np.nan)
    for origin in range(area_count):
        if left[origin] <= 0.0 or math.isnan(world.carriage[origin, area]):
            continue
        row = origin * trade_count + trade
        ask = worth_in(rates, world, origin, trade, practised_wage(results, row))
        if math.isnan(ask):
            continue
        if ask + world.carriage[origin, area] <= bid_worth:
            landed[origin] = ask + world.carriage[origin, area]
            asks[origin] = ask
    lots = 0
    remaining = wanted
    for _pick in range(area_count):
        best = -1
        for origin in range(area_count):
            if not math.isnan(landed[origin]) and (best < 0 or landed[origin] < landed[best]):
                best = origin
        if best < 0 or remaining <= SMALLEST_LOT:
            break
        take = min(remaining, left[best])
        lot_origin[lots], lot_people[lots] = best, take
        lot_ask[lots], lot_carriage[lots] = landed[best] - world.carriage[best, area], world.carriage[best, area]
        lots += 1
        left[best] -= take
        remaining -= take
        landed[best] = np.nan
    return lots


@njit
def _within(lot_people, lot_ask, lot_carriage, lots, ceiling):
    """`formation_bonded._within`: the lots, cheapest first, cut where their cost reaches `ceiling`. Returns how many are kept."""
    spent = 0.0
    for lot in range(lots):
        price = lot_ask[lot] + lot_carriage[lot]
        people = min(lot_people[lot], (ceiling - spent) / price) if price > 0.0 else lot_people[lot]
        if people <= SMALLEST_LOT:
            return lot
        lot_people[lot] = people
        spent += people * price
    return lots


@njit
def buy_bonded(rates, world, results, workers, areas, hired, pool, unassigned, counter, out, area, trade, trade_count, wanted):
    """`formation_bonded.buy`: buy up to `wanted` bonded people of the trade for the area out of `pool` (area x trade: people left,
    drawn down); they join the area's workers and the purchase is recorded in `out`. Returns whether the outputs had room."""
    if wanted <= 0.0 or not world.bondage_allowed[area]:
        return True
    if not pool[:, trade].max() > 0.0:
        return True
    row = area * trade_count + trade
    bid_worth = worth_in(rates, world, area, trade, heading_wage(results, row) if results.cleared[row] else np.nan)
    if math.isnan(bid_worth) or not results.cleared[row]:
        return True
    capacity = world.bid_count[row]
    buyer_employer, buyer_vacant = np.empty(capacity, np.int64), np.empty(capacity)
    buyer_line, buyer_free = np.empty(capacity), np.empty(capacity)
    buyers = _find_buyers(world, results, hired, unassigned, row, buyer_employer, buyer_vacant, buyer_line, buyer_free)
    vacant = python_sum(buyer_vacant, buyers)
    if buyers == 0 or vacant <= 0.0:
        return True
    share = buyer_vacant[:buyers] / vacant
    ceiling = np.inf
    for buyer in range(buyers):
        ceiling = min(ceiling, (buyer_line[buyer] + buyer_free[buyer]) / share[buyer])
    lot_origin, lot_people = np.empty(pool.shape[0], np.int64), np.empty(pool.shape[0])
    lot_ask, lot_carriage = np.empty(pool.shape[0]), np.empty(pool.shape[0])
    lots = _buy_lots(rates, world, results, pool, area, trade, trade_count, min(wanted, vacant / rates.hours), bid_worth, lot_origin, lot_people,
                     lot_ask, lot_carriage)
    kept = _within(lot_people, lot_ask, lot_carriage, lots, ceiling)
    for lot in range(kept):
        pool[lot_origin[lot], trade] -= lot_people[lot]
    for lot in range(kept, lots):
        lot_people[lot] = 0.0
    costs = np.empty(kept)
    for lot in range(kept):
        costs[lot] = lot_people[lot] * (lot_ask[lot] + lot_carriage[lot])
    cost = python_sum(costs, kept)
    for buyer in range(buyers):
        from_free = max(0.0, cost * share[buyer] - buyer_line[buyer])
        unassigned[buyer_employer[buyer]] = max(0.0, unassigned[buyer_employer[buyer]] - from_free)
    bought = python_sum(lot_people, kept)
    if bought > 0.0:
        return _record_purchase(workers, areas, counter, out, area, trade, trade_count, kept, lot_origin, lot_people, lot_ask, lot_carriage,
                                buyers, buyer_employer, share, bought)
    return True


@njit
def _record_purchase(workers, areas, counter, out, area, trade, trade_count, kept, lot_origin, lot_people, lot_ask, lot_carriage, buyers,
                     buyer_employer, share, bought):
    """The bought join the area's workers (the bands share them equally, they are not picked for ability) and the lots, their payers
    and the event are written to the outputs. Returns whether there was room."""
    if out.counts[1] + kept > out.lot_origin.shape[0] or out.counts[2] >= out.purchase_area.shape[0] or out.counts[3] + buyers > out.payer_share.shape[0]:
        return False
    row = area * trade_count + trade
    _name_pair(workers, areas, counter, area, row)
    bands = workers.people.shape[1]
    for band in range(bands):
        workers.people[row, band] += bought / bands
    purchase = out.counts[2]
    out.purchase_area[purchase], out.purchase_trade[purchase] = area, trade
    out.purchase_first[purchase], out.purchase_payers[purchase] = out.counts[3], buyers
    for buyer in range(buyers):
        out.payer_employer[out.counts[3] + buyer], out.payer_share[out.counts[3] + buyer] = buyer_employer[buyer], share[buyer]
    for lot in range(kept):
        slot = out.counts[1] + lot
        out.lot_origin[slot], out.lot_people[slot] = lot_origin[lot], lot_people[lot]
        out.lot_ask[slot], out.lot_carriage[slot], out.lot_purchase[slot] = lot_ask[lot], lot_carriage[lot], purchase
    out.counts[1] += kept
    out.counts[2] += 1
    out.counts[3] += buyers
    return add_event(out, area, trade, BONDED, bought)
