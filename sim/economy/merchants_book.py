"""The merchants' markets packed for their kernels: one slot for each (good, market area), kept while the map, the specs
and the carriage table stay the same objects.

`RouteBook` holds the goods that have two areas or more, their areas, the carriage cost and holding years of every pair
of areas (shared by the goods on one partition, `merchants_search.AreaPack`) and the slot of each (good, area id).
`RoutePass` adds the year's view of the prices; `search` gives a merchant's candidate rows as arrays, best first, the
rule of `merchants.candidate_routes`. The pack never reaches a saved record.
"""
import weakref
from itertools import repeat
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional, Tuple

import numpy as np

from sim.unit_conversions import KILOGRAMS_PER_TONNE

from . import merchants_book_kernel, merchants_search
from .merchant_figures import MarketFigures, market_name

_books: "weakref.WeakKeyDictionary" = weakref.WeakKeyDictionary()


class RouteBook:
    def __init__(self, area_map, specs, carriage):
        self.area_map, self.specs = area_map, specs
        self.goods: List[str] = []
        self.areas: List[tuple] = []
        self.index_of: Dict[str, int] = {}
        packs: List[merchants_search.AreaPack] = []
        pack_index: Dict[int, int] = {}
        good_pack: List[int] = []
        for good in sorted(set(specs) & set(area_map.goods())):
            areas = area_map.areas(good)
            if len(areas) < 2:
                continue
            pack = merchants_search.pack_of(good, areas, carriage)
            position = pack_index.get(id(pack))
            if position is None:
                position = pack_index[id(pack)] = len(packs)
                packs.append(pack)
            self.index_of[good] = len(self.goods)
            self.goods.append(good)
            self.areas.append(areas)
            good_pack.append(position)
        self.packs = packs
        sizes = np.array([len(pack.anchors) for pack in packs], np.int64)
        pair_offset = np.concatenate(([0], np.cumsum(sizes * sizes))).astype(np.int64)
        order_offset = np.concatenate(([0], np.cumsum(sizes))).astype(np.int64)
        self.pair_offset = pair_offset
        self.area_count = np.array([sizes[position] for position in good_pack], np.int64)
        self.pair_base = np.array([pair_offset[position] for position in good_pack], np.int64)
        self.order_base = np.array([order_offset[position] for position in good_pack], np.int64)
        self.slot_base = np.concatenate(([0], np.cumsum(self.area_count)))[:-1].astype(np.int64) if self.goods \
            else np.zeros(0, np.int64)
        self.slots = int(self.area_count.sum())
        self.id_order_flat = (np.concatenate([pack.id_order for pack in packs]) if packs else np.zeros(0, np.int64))
        self.id_rank_flat = np.zeros_like(self.id_order_flat)
        for position, pack in enumerate(packs):
            ranks = np.empty(len(pack.anchors), np.int64)
            ranks[pack.id_order] = np.arange(len(pack.anchors))
            self.id_rank_flat[order_offset[position]:order_offset[position + 1]] = ranks
        self.pack_of_good = np.array(good_pack, np.int64)
        self.spoilage = np.array([specs[good].spoilage_per_year for good in self.goods], np.float64)
        self.unit_mass_kg = np.array([specs[good].unit_mass_kg for good in self.goods], np.float64)
        self.slot_of: Dict[Tuple[str, str], int] = {}
        self.good_of_slot = np.zeros(self.slots, np.int64)
        self.position_of_slot = np.zeros(self.slots, np.int64)
        for good_index, (good, areas) in enumerate(zip(self.goods, self.areas)):
            base = int(self.slot_base[good_index])
            for position, area in enumerate(areas):
                self.slot_of[(good, area.area_id)] = base + position
            self.good_of_slot[base:base + len(areas)] = good_index
            self.position_of_slot[base:base + len(areas)] = np.arange(len(areas))
        self.zeros = np.zeros(self.slots, np.float64)
        self._news: Dict[str, np.ndarray] = {}
        self._market_rows: Dict[int, tuple] = {}
        self.slot_names = [None] * self.slots
        for (good, area_id), slot in self.slot_of.items():
            self.slot_names[slot] = market_name((good, area_id))
        self.scale = None
        self.cost_flat = self.years_flat = None
        self.refresh(carriage)

    def refresh(self, carriage) -> None:
        """The cost and years arrays at the carriage table's present scale."""
        scale = carriage.scale
        if self.scale == scale and self.cost_flat is not None:
            return
        self.scale = scale
        self.cost_flat = (np.concatenate([pack.scaled_cost(carriage).ravel() for pack in self.packs])
                          if self.packs else np.zeros(0, np.float64))
        self.years_flat = (np.concatenate([pack.years.ravel() for pack in self.packs])
                           if self.packs else np.zeros(0, np.int64))

    def fill_years(self, carriage, missing) -> None:
        """Look up the holding years of the pairs the kernel flagged and keep them in the packs."""
        for position, pack in enumerate(self.packs):
            low, high = int(self.pair_offset[position]), int(self.pair_offset[position + 1])
            flagged = missing[low:high]
            if flagged.any():
                pack.fill_years(carriage, flagged)
                self.years_flat[low:high] = pack.years.ravel()

    def market_rows(self, tables) -> np.ndarray:
        """For each slot, its row in the goods-market numbering of `tables` (-1: the market is not numbered). Kept while the
        numbering stays as it is."""
        found = self._market_rows.get(id(tables))
        if found is not None and found[0]() is tables and found[1] == tables.generation:
            return found[2]
        rows = np.array(list(map(tables.goods_numbers.get, self.slot_names, repeat(-1))), np.int64)
        self._market_rows[id(tables)] = (weakref.ref(tables), tables.generation, rows)
        return rows

    def news_current(self, carriage, home_tile) -> np.ndarray:
        """For each slot, whether last year's price there has reached a merchant at `home_tile`."""
        flags = self._news.get(home_tile)
        if flags is None:
            parts = [np.array(merchants_search.news_current_flags(good, areas, carriage, home_tile), np.bool_)
                     for good, areas in zip(self.goods, self.areas)]
            flags = self._news[home_tile] = np.concatenate(parts) if parts else np.zeros(0, np.bool_)
        return flags


def book_for(area_map, specs, carriage) -> RouteBook:
    """The book of these three objects, made again when any is not the one it was made from."""
    try:
        entry = _books.get(carriage)
    except TypeError:
        return RouteBook(area_map, specs, carriage)
    if entry is not None and entry.area_map is area_map and entry.specs is specs \
            and all(pack.current(carriage) for pack in entry.packs):
        entry.refresh(carriage)
        return entry
    book = RouteBook(area_map, specs, carriage)
    _books[carriage] = book
    return book


@dataclass
class RoutePass:
    """The book and the prices a view shows in each slot (0 where it shows none)."""
    book: RouteBook
    view_prices: np.ndarray
    carriage: object
    prepared: dict = field(default_factory=dict)       # rows searched ahead for some merchants (`merchants_batch`), by agent id


def route_pass(view, carriage, area_map, specs) -> RoutePass:
    book = book_for(area_map, specs, carriage)
    prices = np.zeros(book.slots, np.float64)
    for good_index, (good, areas) in enumerate(zip(book.goods, book.areas)):
        base = int(book.slot_base[good_index])
        prices[base:base + len(areas)] = [price or 0.0 for price in view.prices_across(good, areas)]
    return RoutePass(book, prices, carriage)


class DenseShares:
    """What merchants have committed so far this year into and out of each slot (`merchants_shares.RouteShares` over arrays)."""

    def __init__(self, book: RouteBook):
        self.book = book
        self.into = np.zeros(book.slots, np.float64)
        self.out_of = np.zeros(book.slots, np.float64)


@dataclass
class MerchantRows:
    """A merchant's candidate rows, best first: good index, source and destination position and slot, and the rank, price
    here, outlay per unit and most it pays of each."""
    good: np.ndarray
    source: np.ndarray
    destination: np.ndarray
    source_slot: np.ndarray
    destination_slot: np.ndarray
    rank: np.ndarray
    price_here: np.ndarray
    outlay: np.ndarray
    ceiling: np.ndarray


def merchant_array(book: RouteBook, table: Mapping[Tuple[str, str], Optional[float]]) -> np.ndarray:
    """A merchant's figures by (good, area id) in the slots; NaN where it has none. A merchant's own figures
    (`MarketFigures`) are gathered from their column by the slots' market rows."""
    if isinstance(table, MarketFigures):
        return table.take(book.market_rows(table.tables))
    array = np.full(book.slots, np.nan)
    if table:
        slots = np.array(list(map(book.slot_of.get, table, repeat(-1))), np.int64)
        values = np.array(list(table.values()), np.float64)      # a None becomes NaN
        known = slots >= 0
        array[slots[known]] = values[known]
    return array


def search(route: RoutePass, expected: np.ndarray, home_tile, interest_rate: float, margin_share: float,
           good_allowed: Optional[np.ndarray] = None, source_allowed: Optional[np.ndarray] = None) -> MerchantRows:
    """The rows `merchants.candidate_routes` gives for a merchant with these expected prices (NaN: none), sorted by
    rank, then good, source area id and destination area id. An expectation stands in for last year's price where
    there is one; otherwise the view's price counts where the news has reached the merchant."""
    book = route.book
    carriage = route.carriage
    seen = np.where(np.isnan(expected), np.where(book.news_current(carriage, home_tile), route.view_prices, 0.0), expected)
    if good_allowed is None:
        good_allowed = np.ones(len(book.goods), np.bool_)
    if source_allowed is None:
        source_allowed = np.ones(book.slots, np.bool_)
    while True:
        (good, source, destination, rank, price_here, outlay, ceiling, missing) = merchants_book_kernel.search_goods(
            seen, good_allowed, source_allowed, book.slot_base, book.area_count, book.pair_base, book.order_base,
            book.cost_flat, book.years_flat, book.id_order_flat, book.spoilage, book.unit_mass_kg, float(interest_rate),
            float(margin_share), KILOGRAMS_PER_TONNE)
        if not missing.any():
            break
        book.fill_years(carriage, missing)
    order = np.lexsort((book.id_rank_flat[book.order_base[good] + destination],
                        book.id_rank_flat[book.order_base[good] + source], good, rank))
    good, source, destination = good[order], source[order], destination[order]
    return MerchantRows(good, source, destination, book.slot_base[good] + source, book.slot_base[good] + destination,
                        rank[order], price_here[order], outlay[order], ceiling[order])
