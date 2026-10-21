"""`merchants._good_routes` on arrays: the same rows, with the net gap of every (source, destination) pair
worked out at once.

The carriage per tonne between the anchors of a good's areas is a matrix kept per carriage table (and per
scale), so a search spends its time on array arithmetic rather than a dictionary read per pair. The arithmetic
is the scalar search's, operation for operation, so the nets are the same floats. Pairs that pay only after a
haul is held more than a year are corrected one by one in the scalar way, in the scalar order, so ties go to
the same destination.
"""
import math
import weakref

import numpy as np

from sim.unit_conversions import KILOGRAMS_PER_TONNE

from . import merchants_transit

_matrices: "weakref.WeakKeyDictionary" = weakref.WeakKeyDictionary()


def _table_token(carriage):
    """What a kept matrix is valid for: the carriage table's own searched cost tables (None for a carriage that
    does not expose them, whose matrix is rebuilt each time). The scale is applied on top, so a new year's
    scale does not rebuild it."""
    tables = getattr(carriage, "_from_source", None)
    if tables is None:
        return None
    return (id(tables), len(tables))


def _base_matrix(carriage, areas):
    """(areas, token, carriage per tonne between area anchors at the table's scale (rows source, columns
    destination; inf where unreachable), the area ids' alphabetical ranks, the anchors, a table of whole years
    held per pair filled as pairs are met). Kept per carriage table and area tuple."""
    token = _table_token(carriage)
    try:
        by_areas = _matrices.setdefault(carriage, {})
    except TypeError:
        by_areas = {}
    scale = getattr(carriage, "scale", 1.0)
    entry = by_areas.get(id(areas))
    if token is not None and entry is not None and entry[0] is areas and entry[1] == token:
        if entry[6] != scale:                      # the same costs at a new scale: each cost times it, as the table scales them
            entry[2] = entry[7] if scale == 1.0 else entry[7] * scale
            entry[6] = scale
        return entry
    anchors = [area.anchor_tile for area in areas]
    unscaled = getattr(carriage, "_searched_costs_from", carriage.costs_from) if token is not None else carriage.costs_from
    matrix = np.full((len(areas), len(areas)), math.inf)
    for row, anchor in enumerate(anchors):
        costs = unscaled(anchor)
        matrix[row] = [costs.get(tile, math.inf) for tile in anchors]
    ids = [area.area_id for area in areas]
    order = sorted(range(len(ids)), key=ids.__getitem__)
    rank = np.empty(len(ids), dtype=np.int64)
    rank[order] = np.arange(len(ids))
    entry = [areas, token, matrix if token is None or scale == 1.0 else matrix * scale, rank, anchors,
             np.zeros((len(areas), len(areas)), dtype=np.int64), scale if token is not None else 1.0, matrix]
    by_areas[id(areas)] = entry
    return entry


def good_routes(good, spec, areas, prices, carriage, interest_rate, source_ids=None) -> list:
    """Same rows as `merchants._good_routes`, given the price in each area by area id."""
    get_price = prices.get
    return good_routes_aligned(good, spec, areas, [get_price(area.area_id) for area in areas], carriage,
                               interest_rate, source_ids)


def good_routes_aligned(good, spec, areas, seen, carriage, interest_rate, source_ids=None) -> list:
    """Same rows, given the price in each area as a sequence aligned with `areas` (None: no price)."""
    from . import merchants
    margin_share = merchants.MERCHANT_MARGIN_SHARE
    rows = []
    interest = max(0.0, interest_rate)
    spoilage = min(1.0, max(0.0, spec.spoilage_per_year))
    keep = 1.0 - spoilage
    unit_mass = spec.unit_mass_kg
    every_price = np.array(seen, dtype=float)               # None becomes nan
    priced = ~np.isnan(every_price) & (every_price != 0.0)
    if not priced.any():
        return rows
    all_index = np.nonzero(priced)[0]
    price_all = every_price[all_index]
    positive = price_all > 0.0
    if not positive.any():
        return rows
    cheapest = price_all[positive].min()
    dearest = price_all.max()
    cheapest_floor = cheapest * (1.0 + interest + margin_share)
    if dearest * keep - cheapest_floor <= 0.0:
        return rows
    _areas, _token, base, rank, anchors, years_table, *_kept = _base_matrix(carriage, areas)
    kept_price = price_all * keep
    destination_mask = ~(kept_price - cheapest_floor <= 0.0)
    destinations = all_index[destination_mask]
    destination_price = price_all[destination_mask]
    # dearest first, area id breaking ties: the scalar order, so the first of equal nets wins as it does there
    order = np.lexsort((rank[destinations], -destination_price))
    destinations = destinations[order]
    destination_price = destination_price[order]
    destination_spoilage = destination_price * spoilage
    dearest_kept = destination_price[0] * keep
    source_floor = price_all * (1.0 + interest + margin_share)
    source_mask = positive & ~(dearest_kept - source_floor <= 0.0)
    if source_ids is not None:
        source_mask &= np.array([areas[index].area_id in source_ids for index in all_index.tolist()])
    sources = all_index[source_mask]
    if not len(sources):
        return rows
    price_here = price_all[source_mask]
    per_tonne = base[sources[:, None], destinations[None, :]]
    interest_here = price_here * interest
    margin_here = margin_share * price_here
    with np.errstate(invalid="ignore"):                     # a massless good over an unreachable pair is nan, as in the scalar search
        carriage_money = per_tonne * unit_mass / KILOGRAMS_PER_TONNE
        net = (destination_price[None, :] - price_here[:, None]
               - (carriage_money + interest_here[:, None] + destination_spoilage[None, :] + margin_here[:, None]))
    pays = net > 0.0
    pay_rows, pay_columns = np.nonzero(pays)
    if not len(pay_rows):
        return rows
    pay_destinations = destinations[pay_columns]
    pay_sources = sources[pay_rows]
    candidate = net[pays]
    years = _years_held(carriage, years_table, anchors, pay_sources, pay_destinations)
    held_more = years > 1
    if held_more.any():       # a haul held more years pays interest, storage and spoilage for each
        storage_a_year = merchants_transit.storage_per_unit(spec, 2)
        lost_by_years = {held: merchants_transit.lost_share(spec.spoilage_per_year, held) for held in np.unique(years[held_more]).tolist()}
        lost = np.array([lost_by_years.get(held, 0.0) for held in years[held_more].tolist()])
        candidate[held_more] -= ((interest_here[pay_rows[held_more]] + storage_a_year) * (years[held_more] - 1)
                                 + destination_price[pay_columns[held_more]] * (lost - spoilage))
    # each source's first destination (dearest first) of the greatest corrected net, when that net is positive
    starts = np.nonzero(np.concatenate(([True], pay_rows[1:] != pay_rows[:-1])))[0]
    greatest = np.maximum.reduceat(candidate, starts)
    segment_of = np.repeat(np.arange(len(starts)), np.diff(np.append(starts, len(candidate))))
    first = np.nonzero(candidate == greatest[segment_of])[0]
    first = first[np.unique(segment_of[first], return_index=True)[1]]
    first = first[candidate[first] > 0.0]
    if not len(first):
        return rows
    best_net = candidate[first]
    best_row = pay_rows[first]
    best_years = years[first]
    best_there = destination_price[pay_columns[first]]
    carriage_per_unit = per_tonne[pays][first] * unit_mass / KILOGRAMS_PER_TONNE
    here = price_here[best_row]
    outlay = here + carriage_per_unit
    ranks = (-best_net / outlay).tolist()
    # the source price at which the gap just covers carriage, interest, spoilage and margin (merchants._break_even_price)
    lost_kept = {held: 1.0 - merchants_transit.lost_share(spec.spoilage_per_year, held) for held in np.unique(best_years).tolist()}
    storage = {held: merchants_transit.storage_per_unit(spec, held) for held in lost_kept}
    kept = best_there * np.array([lost_kept[held] for held in best_years.tolist()]) - carriage_per_unit
    kept = kept - np.array([storage[held] for held in best_years.tolist()])
    ceiling = (np.maximum(0.0, kept) / (1.0 + max(0.0, interest_rate) * best_years + margin_share)).tolist()
    return [(rank, good, areas[source], areas[destination], price, outlay_each, limit)
            for rank, source, destination, price, outlay_each, limit
            in zip(ranks, sources[best_row].tolist(), pay_destinations[first].tolist(), here.tolist(), outlay.tolist(), ceiling)]


def _years_held(carriage, years_table, anchors, from_index, to_index):
    """`merchants_transit.years_between` of each (from, to) area pair, from a table filled as pairs are met."""
    years = years_table[from_index, to_index]
    for position in np.nonzero(years == 0)[0].tolist():
        source, destination = int(from_index[position]), int(to_index[position])
        held = merchants_transit.years_between(carriage, anchors[source], anchors[destination])
        years_table[source, destination] = years[position] = held
    return years
