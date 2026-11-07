"""What one country's part of the economy shows: its people, its pay, its prices, its output.

Every figure is read from the record of the country's own tiles: its cohorts, the labour markets of its
tiles, the markets its tiles trade in, the producers working on its tiles. Nothing is a home figure scaled
by a ratio. Money is in the economy's unit (the port converts to coin). A figure the country's tiles have
no record of is None, so a caller can fall back to a labelled estimate."""
import math
from typing import Dict, List, Optional, Set, Tuple

from . import carried_book, households
from .home_scope import has_partners
from .market_memory import KEY_SEPARATOR, YearView
from .national_prices import national_prices, national_wages
from .setup import LABOUR_AREA_PREFIX, labour_area
from .types import TileId


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
    tiles = country_tiles(economy, country)
    return national_wages(economy.record, keep=lambda key: _labour_key_in(key, tiles))


def idle_hours_by_trade(economy, country: Optional[str]) -> Dict[str, tuple]:
    """(hours offered and not hired, hours offered) of each trade in the country's labour markets last year:
    the labour core's clearing, summed over the markets."""
    tiles = country_tiles(economy, country)
    idle: Dict[str, float] = {}
    hired: Dict[str, float] = {}
    for key, hours in sorted(economy.record.labour.hours_idle.items()):
        if _labour_key_in(key, tiles):
            trade = key.split(KEY_SEPARATOR, 1)[0]
            idle[trade] = idle.get(trade, 0.0) + hours
            hired[trade] = hired.get(trade, 0.0) + economy.record.labour.hours_cleared_in(key)
    return {trade: (idle[trade], idle[trade] + hired[trade]) for trade in sorted(idle)}


def people_by_trade(economy, country: Optional[str]) -> Dict[str, float]:
    """Working people by trade in the country's labour markets."""
    workers = economy.record.labour.workforce.workers
    totals: Dict[str, float] = {}
    for tile in sorted(country_tiles(economy, country)):
        # each trade is added tile by tile in tile order; the order trades are met in within a tile does not matter
        for trade, bands in workers.get(labour_area(tile), {}).items():
            totals[trade] = totals.get(trade, 0.0) + math.fsum(bands)
    return dict(sorted(totals.items()))


def _area_tiles(economy, good: str) -> Dict[str, Set[TileId]]:
    """Each market area of the good with its tiles; kept on the area map, which does not change once built."""
    return economy.area_map.tile_sets(good)


def prices(economy, country: Optional[str]) -> Dict[str, float]:
    """Each good's price over the market areas that touch the country's tiles (`national_prices.national_prices`;
    every area for None)."""
    if country is None:
        return national_prices(economy.record)
    tiles = country_tiles(economy, country)
    areas_of: Dict[str, Dict[str, Set[TileId]]] = {}

    def touches(good: str, area: str) -> bool:
        by_area = areas_of.get(good)
        if by_area is None:
            by_area = areas_of[good] = _area_tiles(economy, good)
        return area not in by_area or bool(by_area[area] & tiles)
    return national_prices(economy.record, touches)


def traded_volumes(economy, country: Optional[str]) -> Dict[str, float]:
    """Last year's traded quantity of each good over the market areas that touch the country's tiles (every
    market for None)."""
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


def _floor_view(economy):
    setup, record = economy.setup, economy.record
    return YearView(record.memory, record.book, economy.area_map, setup.currency_id, setup, labour_area)


def _tile_floor_costs(economy, view, tile) -> Dict[str, float]:
    return {need.spec.need_id: need.price_index * need.spec.subsistence_per_person
            for need in households.need_prices(economy.setup.basket_for(tile), view, tile)
            if need.spec.subsistence_per_person > 0.0}


def tile_need_floor_costs(economy, tile) -> Dict[str, float]:
    """What one person's floor of each need costs a year at the prices on one tile (the need-basket kernel on
    the tile's own climate floors), whether or not anyone lives there."""
    return _tile_floor_costs(economy, _floor_view(economy), tile)


def need_floor_costs_per_person_year(economy, country: Optional[str]) -> Dict[str, float]:
    """What one person's floor of each need costs a year at the prices the country's households pay, the mean
    over its people (the need-basket kernel on each tile's own climate floors)."""
    record = economy.record
    view = _floor_view(economy)
    sums: Dict[str, float] = {}
    weight = 0.0
    for tile in sorted(country_tiles(economy, country)):
        people = math.fsum(cohort.people for cohort in record.cohorts.values() if cohort.tile == tile)
        if people <= 0.0:
            continue
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
    for producer in economy.record.producers.values():
        if producer.tile not in tiles:
            continue
        recipe = economy.setup.recipes.get(producer.recipe_id)
        if recipe is None:
            continue
        runs = producer.capacity_runs if producer.last_runs < 0.0 else producer.last_runs
        unpriced.update(good for good in recipe.outputs if good not in own_prices)
        values.append(runs * producer.yield_factor * math.fsum(quantity * own_prices[good]
                                                               for good, quantity in recipe.outputs.items() if good in own_prices))
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
    holders += [producer.agent_id for producer in record.producers.values() if producer.tile in tiles]
    return math.fsum(record.book.balance(holder, money) for holder in holders)


def trade_book(economy, country: Optional[str]) -> Dict[str, Dict[str, float]]:
    """What the merchants carried across the country's border last year, by good (tonnes and value each way, in the
    economy's unit; carried_book.trade_book). Empty for None, which has no border."""
    if country is None:
        return {}
    return carried_book.trade_book(economy.record.carriage.carried_goods, economy.setup.country_of, country)
