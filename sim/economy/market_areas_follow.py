"""Carrying the economy's market memory over to a new partition of market areas.

When the built ways change, areas are partitioned again (`EconomySetup.area_map`). What the economy
remembers is keyed by area id, so each new area takes the memory of the old area that held its anchor
tile, good by good. A market whose area no longer exists is dropped; a market that is new starts with
its anchor's old market's values.

Standalone: the area map and market memory of this package.
"""
from typing import Dict, Mapping, Tuple

from .market_areas import AreaMap
from .market_memory import KEY_SEPARATOR, market_key
from .merchants import Merchant
from .record import EconomyRecord

_MEMORY_MARKETS = ("prices", "usual_prices", "volume_weights", "trade_age", "years_without_bids",
                   "years_without_offers")
_RECORD_MARKETS = ("volumes", "margin_years", "curves")


def old_areas_by_new(old: AreaMap, new: AreaMap) -> Dict[str, Dict[str, str]]:
    """{good: {new area id: id of the old area holding its anchor tile}}."""
    return {good: {area.area_id: old.area_of(good, area.anchor_tile) for area in new.areas(good)}
            for good in new.goods()}


def _moved(markets: Mapping[str, object], follows: Mapping[str, Mapping[str, str]],
           old_ids: Mapping[str, frozenset]) -> Dict[str, object]:
    """`markets` (keyed by market_key) with every good's market moved to its new area id; keys that are
    not a good's market (a labour market, say) stay."""
    kept = {}
    for key, value in markets.items():
        first, _separator, area_id = key.partition(KEY_SEPARATOR)
        if first not in follows or area_id not in old_ids[first]:
            kept[key] = value
    for good, new_to_old in follows.items():
        for new_id, old_id in new_to_old.items():
            old_key = market_key(good, old_id)
            if old_key in markets:
                kept[market_key(good, new_id)] = markets[old_key]
    return kept


def _moved_expectations(expected: Mapping[Tuple[str, str], float],
                        follows: Mapping[str, Mapping[str, str]]) -> Dict[Tuple[str, str], float]:
    moved = {pair: value for pair, value in expected.items() if pair[0] not in follows}
    for good, new_to_old in follows.items():
        for new_id, old_id in new_to_old.items():
            if (good, old_id) in expected:
                moved[(good, new_id)] = expected[(good, old_id)]
    return moved


def _merchant_follows(merchant: Merchant, follows: Mapping[str, Mapping[str, str]], new: AreaMap) -> None:
    merchant.expected_prices = _moved_expectations(merchant.expected_prices, follows)
    merchant.expected_volumes = _moved_expectations(merchant.expected_volumes, follows)
    merchant.routes = {route: (destination, new.area_of(route[0], destination) if route[0] in follows else area)
                       for route, (destination, area) in merchant.routes.items()}


def follow(record: EconomyRecord, old: AreaMap, new: AreaMap) -> None:
    """Move the record's market memory, volumes and merchants' expectations from the old partition to the new."""
    follows = old_areas_by_new(old, new)
    old_ids = {good: frozenset(area.area_id for area in old.areas(good)) for good in follows}
    memory = record.memory
    for name in _MEMORY_MARKETS:
        setattr(memory, name, _moved(getattr(memory, name), follows, old_ids))
    for name in _RECORD_MARKETS:
        setattr(record, name, _moved(getattr(record, name), follows, old_ids))
    every_old_id = frozenset().union(*old_ids.values())
    currency_of_area = {area_id: currency for area_id, currency in memory.currency_of_area.items()
                        if area_id not in every_old_id}
    for new_to_old in follows.values():
        for new_id, old_id in new_to_old.items():
            if old_id in memory.currency_of_area:
                currency_of_area[new_id] = memory.currency_of_area[old_id]
    memory.currency_of_area = currency_of_area
    for merchant in record.merchants.values():
        _merchant_follows(merchant, follows, new)
