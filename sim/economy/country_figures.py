"""What one country's part of the economy shows: its people, its pay, its prices, its output.

Every figure is read from the record of the country's own tiles: its cohorts, the labour markets of its
tiles, the markets its tiles trade in, the producers working on its tiles. Nothing is a home figure scaled
by a ratio. Money is in the economy's unit (the port converts to coin). A figure the country's tiles have
no record of is None, so a caller can fall back to a labelled estimate."""
import math
from typing import Dict, Optional, Set

from . import households
from .market_memory import KEY_SEPARATOR, YearView
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
    return economy.setup.civ_id if len(economy.setup.countries()) > 1 else None


def population(economy, country: Optional[str]) -> float:
    tiles = country_tiles(economy, country)
    return math.fsum(cohort.people for cohort in economy.record.cohorts.values() if cohort.tile in tiles)


def _labour_key_in(key: str, tiles: Set[TileId]) -> bool:
    area = key.split(KEY_SEPARATOR, 1)[1]
    return area.startswith(LABOUR_AREA_PREFIX) and area[len(LABOUR_AREA_PREFIX):] in tiles


def wages_per_hour(economy, country: Optional[str]) -> Dict[str, float]:
    """Last year's wage per hour of each trade in the country's labour markets, weighted by the hours hired
    there (the plain mean for a trade that hired nowhere)."""
    tiles = country_tiles(economy, country)
    rows: Dict[str, list] = {}
    for key, wage in economy.record.memory.wages.items():
        if _labour_key_in(key, tiles):
            rows.setdefault(key.split(KEY_SEPARATOR, 1)[0], []).append((wage, economy.record.hours_hired.get(key, 0.0)))
    wages = {}
    for trade, pairs in rows.items():
        hours = math.fsum(weight for _wage, weight in pairs)
        wages[trade] = (math.fsum(wage * weight for wage, weight in pairs) / hours if hours > 0.0
                        else math.fsum(wage for wage, _weight in pairs) / len(pairs))
    return dict(sorted(wages.items()))


def people_by_trade(economy, country: Optional[str]) -> Dict[str, float]:
    """Working people by trade in the country's labour markets."""
    from .labour_state import people_by_trade as in_area
    totals: Dict[str, float] = {}
    for tile in sorted(country_tiles(economy, country)):
        for trade, people in in_area(economy.record.workforce, labour_area(tile)).items():
            totals[trade] = totals.get(trade, 0.0) + people
    return dict(sorted(totals.items()))


def _area_tiles(economy, good: str) -> Dict[str, Set[TileId]]:
    return {area.area_id: set(area.tiles) for area in economy.area_map.areas(good)} if good in economy.area_map.goods() else {}


def prices(economy, country: Optional[str]) -> Dict[str, float]:
    """Each good's price over the market areas that touch the country's tiles, weighted by what each trades
    (this year's volume before any is remembered)."""
    tiles = country_tiles(economy, country)
    record = economy.record
    weights = record.memory.volume_weights or record.volumes
    totals: Dict[str, tuple] = {}
    areas_of: Dict[str, Dict[str, Set[TileId]]] = {}
    for key, price in sorted(record.memory.prices.items()):
        good, area = key.split(KEY_SEPARATOR, 1)
        by_area = areas_of.setdefault(good, _area_tiles(economy, good))
        if area in by_area and not (by_area[area] & tiles):
            continue
        volume = weights.get(key, 0.0)
        value, quantity, plain = totals.get(good, (0.0, 0.0, 0.0))
        totals[good] = (value + price * volume, quantity + volume, plain or price)
    return {good: (value / quantity if quantity > 0.0 else plain) for good, (value, quantity, plain) in sorted(totals.items())}


def need_floor_costs_per_person_year(economy, country: Optional[str]) -> Dict[str, float]:
    """What one person's floor of each need costs a year at the prices the country's households pay, the mean
    over its people (the need-basket kernel on each tile's own climate floors)."""
    setup, record = economy.setup, economy.record
    view = YearView(record.memory, record.book, economy.area_map, setup.currency_id, labour_area)
    sums: Dict[str, float] = {}
    weight = 0.0
    for tile in sorted(country_tiles(economy, country)):
        people = math.fsum(cohort.people for cohort in record.cohorts.values() if cohort.tile == tile)
        if people <= 0.0:
            continue
        weight += people
        for need in households.need_prices(setup.basket_for(tile), view, tile):
            if need.spec.subsistence_per_person > 0.0:
                sums[need.spec.need_id] = sums.get(need.spec.need_id, 0.0) + people * need.price_index * need.spec.subsistence_per_person
    return {need: total / weight for need, total in sorted(sums.items())} if weight > 0.0 else {}


def output_value(economy, country: Optional[str]) -> Optional[float]:
    """What the country's producers make in a year at the country's prices: runs worked last year (capacity
    before they have worked) times a run's outputs. None while no producer works on its tiles."""
    tiles = country_tiles(economy, country)
    own_prices = prices(economy, country)
    total = 0.0
    seen = False
    for producer in economy.record.producers.values():
        if producer.tile not in tiles:
            continue
        recipe = economy.setup.recipes.get(producer.recipe_id)
        if recipe is None:
            continue
        seen = True
        runs = producer.capacity_runs if producer.last_runs < 0.0 else producer.last_runs
        total += runs * producer.yield_factor * math.fsum(quantity * own_prices.get(good, 0.0)
                                                          for good, quantity in recipe.outputs.items())
    return total if seen else None
