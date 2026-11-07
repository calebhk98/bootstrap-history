"""The route search of one good, packed for the kernel (`merchants_kernel`).

For each carriage table the carriage cost between a good's area anchors is packed into a matrix once and kept while the
table's cost dictionaries and scale stay the very objects it was read from; the holding years of each pair are looked
up the first time a haul needs them and kept with it. The pack never reaches a saved record.
"""
import math
import weakref
from typing import Dict, List

import numpy as np

from sim.unit_conversions import KILOGRAMS_PER_TONNE

from . import merchants_kernel, merchants_transit
from .tile_costs import CarriageTable

_packs: "weakref.WeakKeyDictionary" = weakref.WeakKeyDictionary()


class AreaPack:
    """Areas as arrays: anchors, the cost matrix, the holding years of each pair and the order by id. Goods that share
    a partition of the map (the same area ids and anchors) share a pack."""

    def __init__(self, areas, carriage):
        self.shape = shape_of(areas)
        self.unscaled = isinstance(carriage, CarriageTable)      # its costs are kept before the year's scale, which moves every year
        self.scale = 1.0 if self.unscaled else carriage.scale
        self.anchors = self.shape[1]
        self.tables = [carriage.unscaled_costs_from(anchor) if self.unscaled else carriage.costs_from(anchor)
                       for anchor in self.anchors]
        self._scaled = (None, None)
        size = len(areas)
        self.cost = np.full((size, size), math.inf)
        for row, table in enumerate(self.tables):
            get = table.get
            self.cost[row] = [get(anchor, math.inf) for anchor in self.anchors]
        self.years = np.zeros((size, size), np.int64)
        self.news_current: Dict[str, List[bool]] = {}     # by home tile: whether each area's last price has reached it
        self.id_order = np.array(sorted(range(size), key=lambda position: self.shape[0][position]), np.int64)

    def scaled_cost(self, carriage):
        """The cost matrix at the table's present scale."""
        if not self.unscaled or carriage.scale == 1.0:
            return self.cost
        if self._scaled[0] != carriage.scale:
            self._scaled = (carriage.scale, self.cost * carriage.scale)
        return self._scaled[1]

    def current(self, carriage) -> bool:
        """Whether the pack still describes this table: for a table that hands out new cost dictionaries, every
        source's dictionary and its scale."""
        if self.unscaled:
            return isinstance(carriage, CarriageTable)
        if self.scale != carriage.scale:
            return False
        return all(carriage.costs_from(anchor) is table for anchor, table in zip(self.anchors, self.tables))

    def fill_years(self, carriage, missing) -> None:
        """Look up the holding years of the pairs the kernel flagged."""
        size = len(self.anchors)
        for flat in np.flatnonzero(missing):
            source, destination = divmod(int(flat), size)
            self.years[source, destination] = merchants_transit.years_between(
                carriage, self.anchors[source], self.anchors[destination])


def shape_of(areas) -> tuple:
    """(area ids, anchor tiles) of the areas: what the arrays of a pack depend on besides the table."""
    return tuple(area.area_id for area in areas), tuple(area.anchor_tile for area in areas)


class _Packs:
    def __init__(self):
        self.by_good: Dict[str, tuple] = {}      # good -> (its areas tuple, the pack)
        self.by_shape: Dict[tuple, AreaPack] = {}


def pack_of(good, areas, carriage) -> AreaPack:
    """The pack of the good's areas for this carriage table, rebuilt when the table moved; a table that cannot be
    weakly held keeps nothing."""
    try:
        kept = _packs.get(carriage)
        if kept is None:
            kept = _packs[carriage] = _Packs()
    except TypeError:
        return AreaPack(areas, carriage)
    entry = kept.by_good.get(good)
    if entry is not None and entry[0] is areas and entry[1].current(carriage):
        return entry[1]
    shape = shape_of(areas)
    pack = kept.by_shape.get(shape)
    if pack is None or not pack.current(carriage):
        old = pack
        pack = kept.by_shape[shape] = AreaPack(areas, carriage)
        if old is not None:
            pack.years, pack.news_current = old.years, old.news_current     # these depend on the tiles only
    kept.by_good[good] = (areas, pack)
    return pack


def good_routes(good, spec, areas, prices, carriage, interest_rate, margin_share, source_ids=None) -> List[tuple]:
    """The unsorted rows (rank, good, source area, destination area, price here, outlay per unit, most it pays) of the
    good's paying hauls, given its price in each area (by area id); with `source_ids` only those source areas."""
    if len(areas) == 0:
        return []
    pack = pack_of(good, areas, carriage)
    price_array = np.array([prices.get(area.area_id) or 0.0 for area in areas])
    allowed = np.array([source_ids is None or area.area_id in source_ids for area in areas], np.bool_)
    while True:
        count, sources, destinations, ranks, prices_here, outlays, ceilings, missing = merchants_kernel.search_good(
            price_array, pack.scaled_cost(carriage), pack.years, pack.id_order, allowed, float(interest_rate),
            float(spec.spoilage_per_year), float(spec.unit_mass_kg), float(margin_share), KILOGRAMS_PER_TONNE)
        if not missing.any():
            break
        pack.fill_years(carriage, missing)
    sources, destinations = sources[:count].tolist(), destinations[:count].tolist()
    ranks, prices_here, outlays, ceilings = (column[:count].tolist() for column in (ranks, prices_here, outlays, ceilings))
    return [(ranks[row], good, areas[sources[row]], areas[destinations[row]], prices_here[row], outlays[row],
             ceilings[row]) for row in range(count)]


def news_current_flags(good, areas, carriage, home_tile) -> List[bool]:
    """For each area, whether last year's price there has reached a merchant at `home_tile` (the haul to it is held a
    year or less)."""
    pack = pack_of(good, areas, carriage)
    flags = pack.news_current.get(home_tile)
    if flags is None:
        flags = pack.news_current[home_tile] = [
            merchants_transit.news_lag(carriage, home_tile, anchor) == 0 for anchor in pack.anchors]
    return flags
