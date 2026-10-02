"""Market areas: which tiles share one price for a good.

A good's market area is the set of tiles whose carriage to the area's anchor costs less than a share
of the good's value, so a price gap inside an area is bounded by carriage. Silver spans a
civilisation; grain stays within a tile or a few. Goods of similar value per tonne share one
partition (log-scale buckets), so the map holds a few partitions, not one per good.

Standalone: `sim.constants` and `sim.economy.types` only.
"""
import math
from dataclasses import replace
from typing import Dict, Iterable, List, Mapping, Tuple

from sim.constants import declare
from sim.economy.tile_costs import CarriageTable
from sim.economy.types import AreaId, GoodId, GoodSpec, MarketArea, TileId

KILOGRAMS_PER_TONNE = 1000.0

MARKET_AREA_THRESHOLD_SHARE = declare(
    "MARKET_AREA_THRESHOLD_SHARE", 0.15, kind="temporary_heuristic",
    unit="share of a good's value per tonne", source=None, confidence="D",
    why="Price gaps within a market are bounded by carriage; tiles whose carriage to the anchor is "
        "under this share of the value trade as one market. Not yet derived from trader margins "
        "and arbitrage speed.")
MARKET_AREA_VALUE_BUCKET_WIDTH_LN = declare(
    "MARKET_AREA_VALUE_BUCKET_WIDTH_LN", 1.4, kind="temporary_heuristic",
    unit="natural-log units of value per tonne", source=None, confidence="D",
    why="Goods whose value per tonne lies within one bucket share a partition, trading some "
        "precision in the area boundary for a few partitions instead of one per good.")
FREE_BUCKET = "free"


def partition(tiles: Iterable[TileId], carriage: CarriageTable, value_per_tonne: float,
              population_by_tile: Mapping[TileId, float], threshold_share: float = MARKET_AREA_THRESHOLD_SHARE,
              label: str = "") -> Tuple[MarketArea, ...]:
    """Group `tiles` into areas. Tiles are taken most populous first (ties by id); each joins the
    cheapest existing anchor whose carriage is within `threshold_share` of `value_per_tonne`,
    else becomes an anchor. `label` names the good (or bucket); the area id is anchor@label."""
    limit = threshold_share * max(0.0, value_per_tonne)
    ordered = sorted(tiles, key=lambda tile_id: (-population_by_tile.get(tile_id, 0.0), tile_id))
    anchors: List[TileId] = []
    members: Dict[TileId, List[TileId]] = {}
    for tile_id in ordered:
        best_anchor, best_cost = None, math.inf
        for anchor in anchors:
            cost = carriage.cost_per_tonne(tile_id, anchor)
            if cost <= limit and cost < best_cost:
                best_anchor, best_cost = anchor, cost
        if best_anchor is None:
            anchors.append(tile_id)
            members[tile_id] = [tile_id]
        else:
            members[best_anchor].append(tile_id)
    return tuple(MarketArea(area_id="%s@%s" % (anchor, label), good_id=label,
                            tiles=tuple(sorted(members[anchor])), anchor_tile=anchor)
                 for anchor in sorted(anchors))


def value_per_tonne(spec: GoodSpec, price_per_unit: float) -> float:
    return price_per_unit * KILOGRAMS_PER_TONNE / spec.unit_mass_kg


def bucket_of(value: float, width_ln: float = MARKET_AREA_VALUE_BUCKET_WIDTH_LN) -> Tuple[str, float]:
    """(label, representative value per tonne) of the log-scale bucket holding `value`."""
    if value <= 0.0:
        return FREE_BUCKET, 0.0
    index = round(math.log(value) / width_ln)
    return "b%d" % index, math.exp(index * width_ln)


class AreaMap:
    """Market areas for a set of goods at current prices, shared by goods in one value bucket."""

    def __init__(self, tiles: Iterable[TileId], carriage: CarriageTable,
                 goods: Iterable[Tuple[GoodSpec, float]], population_by_tile: Mapping[TileId, float],
                 threshold_share: float = MARKET_AREA_THRESHOLD_SHARE,
                 bucket_width_ln: float = MARKET_AREA_VALUE_BUCKET_WIDTH_LN):
        tile_ids = tuple(tiles)
        self._partitions: Dict[str, Tuple[MarketArea, ...]] = {}
        self._bucket_of_good: Dict[GoodId, str] = {}
        self._area_of_tile: Dict[str, Dict[TileId, AreaId]] = {}
        for spec, price in goods:
            label, representative = bucket_of(value_per_tonne(spec, price), bucket_width_ln)
            self._bucket_of_good[spec.good_id] = label
            if label not in self._partitions:
                areas = partition(tile_ids, carriage, representative, population_by_tile,
                                  threshold_share, label)
                self._partitions[label] = areas
                self._area_of_tile[label] = {tile: area.area_id for area in areas for tile in area.tiles}

    def goods(self) -> Tuple[GoodId, ...]:
        return tuple(sorted(self._bucket_of_good))

    def bucket_count(self) -> int:
        return len(self._partitions)

    def areas(self, good: GoodId) -> Tuple[MarketArea, ...]:
        label = self._bucket_of_good[good]
        return tuple(replace(area, good_id=good) for area in self._partitions[label])

    def area_of(self, good: GoodId, tile: TileId) -> AreaId:
        """The id of the area holding `tile` for `good`; KeyError if either is unknown."""
        return self._area_of_tile[self._bucket_of_good[good]][tile]

    def market_area_of(self, good: GoodId, tile: TileId) -> MarketArea:
        area_id = self.area_of(good, tile)
        return next(area for area in self.areas(good) if area.area_id == area_id)
