"""What it costs to move a tonne between tiles: cheapest paths over geography's route graph.

Space is tiles. The links (land, river, coast, open sea), their lengths, grades and which modes run on
them belong to geography (`sim.geography.api.route_costs`); this module only holds the caller's money per
tonne-km of each carriage mode (by geography mode id: `cart`, `pack`, `river_boat`, `sail`, ...) and
handling per tonne, and caches the cheapest cost from each source tile among the tiles it was given.
Paths may leave the given tiles (a road through a neighbour); only the given tiles are answered.

Standalone: `sim.geography.api` and `sim.economy.types` only.
"""
import math
from typing import Dict, Iterable, Mapping, Optional

from sim.economy.types import TileId, TileSpec
from sim.geography.api import layer_value, map_of_tiles, route_costs, tile_facts


def tiles_from_geography(geography: dict, tile_ids: Iterable[TileId]) -> Dict[TileId, TileSpec]:
    """TileSpecs for the named tiles from the parsed geography document; borders are kept whole."""
    records = geography["land_tiles"]["tiles"]
    result = {}
    for tile_id in tile_ids:
        record = records[tile_id]
        result[tile_id] = TileSpec(
            tile_id=tile_id, latitude=record["lat"], longitude=record["lon"],
            land_area_km2=record["land_area_km2"], coastal=bool(record["coastal"]),
            borders=tuple(record["borders"]), arable_fraction=record["arable_fraction"],
            fertility=record["fertility_quality_multiplier"],
            climate_class=str(record.get("koppen_class") or ""))
    return result


def tiles_from_map(world_map, tile_ids: Iterable[TileId]) -> Dict[TileId, TileSpec]:
    """TileSpecs for the named tiles read through geography's api from `world_map`; borders are kept whole."""
    result = {}
    for tile_id in tile_ids:
        facts = tile_facts(tile_id, world_map)
        result[tile_id] = TileSpec(
            tile_id=tile_id, latitude=facts["lat"], longitude=facts["lon"],
            land_area_km2=facts["land_area_km2"], coastal=facts["coastal"],
            borders=tuple(facts["neighbours"]), arable_fraction=layer_value(tile_id, "arable_fraction", world_map),
            fertility=layer_value(tile_id, "fertility_quality_multiplier", world_map),
            climate_class=str(facts["climate_class"] or ""))
    return result


def world_map_of(tiles: Mapping[TileId, TileSpec]):
    """A geography map of exactly these tiles, for a scenario whose tiles are not on the base map."""
    return map_of_tiles({
        tile_id: {"lat": tile.latitude, "lon": tile.longitude, "land_area_km2": tile.land_area_km2,
                  "coastal": tile.coastal, "borders": list(tile.borders)}
        for tile_id, tile in tiles.items()})


class CarriageTable:
    """Cheapest money cost per tonne between tiles over geography's route graph.

    Costs from a source tile are computed on first use and cached; `warm()` fills every source.
    `world_map` is geography's map (the base map when None); `held_nodes` are the tech nodes the
    society holds, which open-sea lanes may require."""

    def __init__(self, tile_ids: Iterable[TileId], money_per_tonne_km_by_mode: Mapping[str, float],
                 handling_money_per_tonne_by_mode: Optional[Mapping[str, float]] = None,
                 held_nodes: Iterable[str] = (), world_map=None):
        self.tile_ids = tuple(sorted(tile_ids))
        self._tile_set = frozenset(self.tile_ids)
        self._rates = dict(money_per_tonne_km_by_mode)
        self._handling = dict(handling_money_per_tonne_by_mode or {})
        self._held_nodes = tuple(sorted(held_nodes))
        self._world_map = world_map
        self._from_source: Dict[TileId, Dict[TileId, float]] = {}

    def costs_from(self, source: TileId) -> Dict[TileId, float]:
        """Cheapest cost to every given tile reachable from `source` (unreachable tiles are absent)."""
        cached = self._from_source.get(source)
        if cached is None:
            everywhere = route_costs(
                [source], sorted(self._rates), mode_costs=self._rates, handling_costs=self._handling,
                held_nodes=self._held_nodes, world_map=self._world_map)
            cached = {tile_id: cost for tile_id, cost in everywhere.items() if tile_id in self._tile_set}
            self._from_source[source] = cached
        return cached

    def cost_per_tonne(self, from_tile: TileId, to_tile: TileId) -> float:
        """Money per tonne by the cheapest path; infinite when no path exists."""
        return self.costs_from(from_tile).get(to_tile, math.inf)

    def warm(self) -> None:
        for tile_id in self.tile_ids:
            self.costs_from(tile_id)


def carriage_table(tiles: Mapping[TileId, TileSpec], money_per_tonne_km_by_mode: Mapping[str, float],
                   handling_money_per_tonne_by_mode: Optional[Mapping[str, float]] = None,
                   held_nodes: Iterable[str] = (), world_map=None) -> CarriageTable:
    """A table over these tiles at the given rates."""
    return CarriageTable(tiles, money_per_tonne_km_by_mode, handling_money_per_tonne_by_mode, held_nodes, world_map)
