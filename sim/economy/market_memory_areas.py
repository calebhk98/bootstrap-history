"""Numbering the market memory's goods markets for a whole partition of market areas at once.

A market's number is its place in the order markets were first numbered, so the order must not be the order writers happened to
touch them in. Every market an area map defines is numbered here as one sorted batch, when the areas are drawn (the opening, a
load, a redraw); a single write to a market outside the map is the only thing left that numbers one at a time."""
from typing import List

from .market_areas import AreaMap
from .market_memory import MarketMemory, market_key


def area_market_keys(area_map: AreaMap) -> List[str]:
    """Every goods market (`good|area`) the area map defines."""
    return [market_key(good, area.area_id) for good in area_map.goods() for area in area_map.areas(good)]


def number_area_markets(memory: MarketMemory, area_map: AreaMap) -> None:
    """Number the area map's goods markets that are not numbered yet, as one sorted batch."""
    memory.tables.admit_goods_markets(area_market_keys(area_map))
