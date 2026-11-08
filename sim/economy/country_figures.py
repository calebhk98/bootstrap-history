"""What one country's part of the economy shows: its people, its pay, its prices, its output.

Every figure is read from the record of the country's own tiles: its cohorts, the labour markets of its
tiles, the markets its tiles trade in, the producers working on its tiles. Nothing is a home figure scaled
by a ratio. Money is in the economy's unit (the port converts to coin). A figure the country's tiles have
no record of is None, so a caller can fall back to a labelled estimate."""
import math
import weakref
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

from sim.labour.api import people_by_trade_over

from . import carried_book, households_basket, quiet_year
from .home_scope import has_partners
from .market_memory import KEY_SEPARATOR, YearView
from .national_prices import national_prices, national_wages
from .price_index_masks import country_price_mask, labour_area_mask
from .setup import LABOUR_AREA_PREFIX, labour_area
from .types import TileId


class _Identity:
    """An object as a dictionary key by identity; holding it keeps its address from being reused while it is a key."""

    def __init__(self, held) -> None:
        self.held = held

    def __hash__(self) -> int:
        return id(self.held)

    def __eq__(self, other) -> bool:
        return isinstance(other, _Identity) and other.held is self.held


def country_tiles(economy, country: Optional[str]) -> Set[TileId]:
    """The tiles of `country` (every tile for None)."""
    setup = economy.setup
    return set(setup.tiles) if country is None else set(setup.tiles_of(country))


def home_when_shared(economy, country: Optional[str]) -> Optional[str]:
    """The country a question about 'the economy' is about: the one asked for; the home country when the
    economy holds several; None (everything) when it holds only the home one."""
    if country is not None:
        return country
    return economy.setup.civ_id if has_partners(economy.setup) else None


def population(economy, country: Optional[str]) -> float:
    tiles = country_tiles(economy, country)
    return math.fsum(cohort.people for cohort in economy.record.cohorts.values() if cohort.tile in tiles)


def _labour_key_in(key: str, tiles: Set[TileId]) -> bool:
    area = key.split(KEY_SEPARATOR, 1)[1]
    return area.startswith(LABOUR_AREA_PREFIX) and area[len(LABOUR_AREA_PREFIX):] in tiles


def wages_per_hour(economy, country: Optional[str]) -> Dict[str, float]:
    """The wage per hour of each trade over the country's labour areas (`national_prices.national_wages`)."""
    def compute():
        tiles = country_tiles(economy, country)
        return national_wages(economy.record, keep_token=frozenset(tiles), keep_mask=lambda layout: labour_area_mask(layout, tiles))
    return dict(quiet_year.kept(economy, ("wages", country), compute))


def idle_hours_by_trade(economy, country: Optional[str]) -> Dict[str, tuple]:
    """(hours offered and not hired, hours offered) of each trade in the country's labour markets last year:
    the labour core's clearing, summed over the markets."""
    def compute():
        tiles = country_tiles(economy, country)
        idle: Dict[str, float] = {}
        hired: Dict[str, float] = {}
        keys = [key for key in sorted(economy.record.labour.hours_idle) if _labour_key_in(key, tiles)]
        for key, hours_hired in zip(keys, economy.record.labour.hours_cleared_in_markets(keys)):
            trade = key.split(KEY_SEPARATOR, 1)[0]
            idle[trade] = idle.get(trade, 0.0) + economy.record.labour.hours_idle[key]
            hired[trade] = hired.get(trade, 0.0) + hours_hired
        return {trade: (idle[trade], idle[trade] + hired[trade]) for trade in sorted(idle)}
    return dict(quiet_year.kept(economy, ("idle", country), compute))


def people_by_trade(economy, country: Optional[str]) -> Dict[str, float]:
    """Working people by trade in the country's labour markets."""
    # each trade is added tile by tile in tile order
    return people_by_trade_over(economy.record.labour.workforce, [labour_area(tile) for tile in sorted(country_tiles(economy, country))])


def _area_tiles(economy, good: str) -> Dict[str, Set[TileId]]:
    """Each market area of the good with its tiles; kept on the area map, which does not change once built."""
    return economy.area_map.tile_sets(good)


def prices(economy, country: Optional[str]) -> Dict[str, float]:
    """Each good's price over the market areas that touch the country's tiles (`national_prices.national_prices`;
    every area for None)."""
    return dict(quiet_year.kept(economy, ("prices", country), lambda: _prices(economy, country)))


def _prices(economy, country: Optional[str]) -> Dict[str, float]:
    if country is None:
        return national_prices(economy.record)
    tiles = country_tiles(economy, country)
    token = (_Identity(economy.area_map), frozenset(tiles))
    if hasattr(economy.area_map, "tile_table"):
        table = economy.area_map.tile_table()
        return national_prices(economy.record, keep_token=token, keep_mask=lambda layout: country_price_mask(layout, table, tiles))
    areas_of: Dict[str, Dict[str, Set[TileId]]] = {}

    def touches(good: str, area: str) -> bool:      # an area map that is not an `AreaMap` (a test's stand-in)
        by_area = areas_of.get(good)
        if by_area is None:
            by_area = areas_of[good] = _area_tiles(economy, good)
        return area not in by_area or bool(by_area[area] & tiles)
    return national_prices(economy.record, touches, keep_token=token)


def traded_volumes(economy, country: Optional[str]) -> Dict[str, float]:
    """Last year's traded quantity of each good over the market areas that touch the country's tiles (every
    market for None)."""
    return dict(quiet_year.kept(economy, ("volumes", country), lambda: _traded_volumes(economy, country)))


def _traded_volumes(economy, country: Optional[str]) -> Dict[str, float]:
    tiles = country_tiles(economy, country)
    totals: Dict[str, float] = {}
    areas_of: Dict[str, Dict[str, Set[TileId]]] = {}
    for key, volume in sorted(economy.record.goods.volumes.items()):
        good, area = key.split(KEY_SEPARATOR, 1)
        if country is not None:
            by_area = areas_of.get(good)
            if by_area is None:
                by_area = areas_of[good] = _area_tiles(economy, good)
            if area in by_area and not (by_area[area] & tiles):
                continue
        totals[good] = totals.get(good, 0.0) + volume
    return totals


def opening_basket(economy, country: Optional[str]) -> Dict[str, float]:
    """The opening basket's part for the country: what the economy's producers supplied of each good, shared
    out in proportion to the demand each country's households were seeded with (the whole basket for None)."""
    record = economy.record
    if country is None:
        return dict(record.goods.opening_basket)
    wanted = record.goods.opening_demand_by_country.get(country, {})
    basket = {}
    for good, supplied in record.goods.opening_basket.items():
        total = record.goods.opening_demand.get(good, 0.0)
        if total > 0.0 and wanted.get(good, 0.0) > 0.0:
            basket[good] = supplied * wanted[good] / total
    return basket


_floor_views: "weakref.WeakKeyDictionary" = weakref.WeakKeyDictionary()


def _floor_view(economy):
    """The view the floor costs are read from, kept for the economy while its memory, book and area map are the same objects
    and in the same year (its kept reads are dropped on every write to the memory, so a new view is not needed for that)."""
    setup, record = economy.setup, economy.record
    inputs = (record.memory, record.book, economy.area_map, setup)
    try:
        kept = _floor_views.get(economy)
    except TypeError:
        kept = None
    if kept is not None and kept[0] == record.memory.year and all(old is new for old, new in zip(kept[1], inputs)):
        return kept[2]
    view = YearView(record.memory, record.book, economy.area_map, setup.currency_id, setup, labour_area)
    try:
        _floor_views[economy] = (record.memory.year, inputs, view)
    except TypeError:
        pass
    return view


def _tile_floor_costs(economy, view, tile) -> Dict[str, float]:
    """The tile's floor cost of each need, worked out once per tile while the economy stands between steps (callers read, never change, it)."""
    return quiet_year.kept(economy, ("tile_floor_costs", tile), lambda: _worked_tile_floor_costs(economy, view, tile))


def _worked_tile_floor_costs(economy, view, tile) -> Dict[str, float]:
    return {need.spec.need_id: need.price_index * need.spec.subsistence_per_person
            for need in households_basket.tile_need_prices(economy.setup, view, tile)
            if need.spec.subsistence_per_person > 0.0}


def tile_need_floor_costs(economy, tile) -> Dict[str, float]:
    """What one person's floor of each need costs a year at the prices on one tile (the need-basket kernel on
    the tile's own climate floors), whether or not anyone lives there."""
    return dict(_tile_floor_costs(economy, _floor_view(economy), tile))


def need_floor_costs_per_person_year(economy, country: Optional[str]) -> Dict[str, float]:
    """What one person's floor of each need costs a year at the prices the country's households pay, the mean
    over its people (the need-basket kernel on each tile's own climate floors)."""
    return dict(quiet_year.kept(economy, ("need_floor_costs", country), lambda: _worked_need_floor_costs(economy, country)))


def _worked_need_floor_costs(economy, country: Optional[str]) -> Dict[str, float]:
    record = economy.record
    view = _floor_view(economy)
    people_on: Dict[TileId, List[float]] = {}
    for cohort in record.cohorts.values():
        people_on.setdefault(cohort.tile, []).append(cohort.people)
    tiles = [tile for tile in sorted(country_tiles(economy, country)) if math.fsum(people_on.get(tile, ())) > 0.0]
    households_basket.tiles_need_prices(economy.setup, view, tiles)     # every tile's basket priced together; the reads below are then kept ones
    sums: Dict[str, float] = {}
    weight = 0.0
    for tile in tiles:
        people = math.fsum(people_on[tile])
        weight += people
        for need_id, cost in _tile_floor_costs(economy, view, tile).items():
            sums[need_id] = sums.get(need_id, 0.0) + people * cost
    return {need: total / weight for need, total in sorted(sums.items())} if weight > 0.0 else {}


def output_value(economy, country: Optional[str]) -> Optional[float]:
    """`output_value_and_unpriced` without the unpriced goods."""
    return output_value_and_unpriced(economy, country)[0]


def output_value_and_unpriced(economy, country: Optional[str]) -> Tuple[Optional[float], List[str]]:
    """(what the country's producers make in a year at the country's prices, the goods they make that have no price
    there, sorted). Runs worked last year (capacity before they have worked) times a run's outputs; an output with no
    price is left out of the value and named in the list. The value is None while no producer works on its tiles."""
    tiles = country_tiles(economy, country)
    own_prices = prices(economy, country)
    values = []
    unpriced = set()
    run_value: Dict[str, Optional[float]] = {}       # per recipe: what one run's outputs are worth at the country's prices (None: the recipe is unknown)
    store = economy.record.producers
    table = store.table
    rows = store.live_rows()
    tile_names, recipe_names = store.names["tiles"].name_list, store.names["recipes"].name_list
    inside = np.array([name in tiles for name in tile_names], dtype=np.bool_)
    rows = rows[inside[table.tile[rows]]]
    for row, recipe_number, capacity, last_runs, yield_factor in zip(
            rows.tolist(), table.recipe[rows].tolist(), store.floats("capacity_runs", rows), store.floats("last_runs", rows),
            store.floats("yield_factor", rows)):
        recipe_id = recipe_names[recipe_number]
        if recipe_id not in run_value:
            recipe = economy.setup.recipes.get(recipe_id)
            run_value[recipe_id] = None if recipe is None else math.fsum(
                quantity * own_prices[good] for good, quantity in recipe.outputs.items() if good in own_prices)
            if recipe is not None:
                unpriced.update(good for good in recipe.outputs if good not in own_prices)
        if run_value[recipe_id] is None:
            continue
        runs = capacity if last_runs < 0.0 else last_runs
        values.append(runs * yield_factor * run_value[recipe_id])
    # fsum is exact, so the producers' order (creation order live, saved order after a load) cannot change the total
    return (math.fsum(values) if values else None), sorted(unpriced)


def currency(economy):
    """The money standard the one economy uses (regime, backing good and amount)."""
    return economy.record.currency


def money_held(economy, country: Optional[str]) -> float:
    """The money held by the household cohorts and producers on the country's tiles."""
    tiles = country_tiles(economy, country)
    record = economy.record
    money = economy.setup.currency_id
    holders = [cohort.agent_id for cohort in record.cohorts.values() if cohort.tile in tiles]
    holders += record.producers.ids_on_tiles(tiles.__contains__)
    return math.fsum(record.book.balance(holder, money) for holder in holders)


def trade_book(economy, country: Optional[str]) -> Dict[str, Dict[str, float]]:
    """What the merchants carried across the country's border last year, by good (tonnes and value each way, in the
    economy's unit; carried_book.trade_book). Empty for None, which has no border."""
    if country is None:
        return {}
    return carried_book.trade_book(economy.record.carriage.carried_goods, economy.setup.country_of, country)
