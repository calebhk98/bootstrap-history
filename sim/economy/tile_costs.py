"""What it costs to move a tonne between tiles: cheapest paths over geography's route graph.

Space is tiles. The links (land, river, coast, open sea), their lengths, grades and which modes run on
them belong to geography (`sim.geography.api.route_costs`); this module only holds the caller's money per
tonne-km of each carriage mode (by geography mode id: `cart`, `pack`, `river_boat`, `sail`, ...) and
handling per tonne, and caches the cheapest cost from each source tile among the tiles it was given.
Paths may leave the given tiles (a road through a neighbour); only the given tiles are answered.

Standalone: `sim.geography.api` and `sim.economy.types` only.
"""
import dataclasses
import math
from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Optional, Tuple

from sim.economy import carriage_cache
from sim.economy.types import HECTARES_PER_SQUARE_KILOMETRE, TileId, TileSpec
from sim.geography.api import crop_site, map_of_tiles, open_map, route, route_costs, tile_facts


def tiles_from_map(world_map, tile_ids: Iterable[TileId], open_field_cropped_share: float,
                   tillage_capacity: float = 1.0) -> Dict[TileId, TileSpec]:
    """TileSpecs for the named tiles read through geography's api from `world_map`; borders are kept whole.
    A tile's land is geography's cropland under a rotation that crops `open_field_cropped_share` of open fields
    each year, and its fertility the yield factor of a cropped hectare (soil, climate, river water)."""
    result = {}
    for tile_id in tile_ids:
        facts = tile_facts(tile_id, world_map)
        site = crop_site(tile_id, open_field_cropped_share, world_map, tillage_capacity=tillage_capacity)
        result[tile_id] = following_site(TileSpec(
            tile_id=tile_id, latitude=facts["lat"], longitude=facts["lon"],
            land_area_km2=facts["land_area_km2"], coastal=facts["coastal"],
            borders=tuple(facts["neighbours"]), cropped_fraction=0.0, fertility=0.0,
            climate_class=str(facts["climate_class"] or "")), site)
    return result


def following_site(tile: TileSpec, site) -> TileSpec:
    """The tile with its cropped share and fertility read from a crop site (geography's `crop_site`)."""
    area_hectares = tile.land_area_km2 * HECTARES_PER_SQUARE_KILOMETRE
    cropped_hectares = site.cropped_hectares if site.yield_factor > 0.0 else 0.0   # ground that yields nothing is not cropland
    return dataclasses.replace(tile, cropped_fraction=cropped_hectares / area_hectares if area_hectares > 0.0 else 0.0,
                               fertility=site.yield_factor)


def world_map_of(tiles: Mapping[TileId, TileSpec]):
    """A geography map of exactly these tiles, for a scenario whose tiles are not on the base map."""
    return map_of_tiles({
        tile_id: {"lat": tile.latitude, "lon": tile.longitude, "land_area_km2": tile.land_area_km2,
                  "coastal": tile.coastal, "borders": list(tile.borders)}
        for tile_id, tile in tiles.items()})


@dataclass(frozen=True)
class Haul:
    """How the cheapest path between two tiles is travelled: its days, the money a tonne pays on each carriage
    mode's legs (the handling of a change to the mode included) and how many times the load is handled into
    each mode."""
    days: float
    money_by_mode: Tuple[Tuple[str, float], ...] = ()
    handlings_by_mode: Tuple[Tuple[str, int], ...] = ()
    km_by_mode: Tuple[Tuple[str, float], ...] = ()          # kilometres a tonne is carried on each mode (geography's)
    team_days_by_mode: Tuple[Tuple[str, float], ...] = ()   # working days of a team a tonne takes on each mode (geography's rates)


NO_PATH = Haul(math.inf)


def haul_of(hauled: Mapping[str, object]) -> Haul:
    """The `Haul` of a geography route: a load is handled into the first leg's mode and into each leg whose mode
    differs from the one before."""
    money: Dict[str, float] = {}
    handlings: Dict[str, int] = {}
    previous = None
    for leg in hauled["legs"]:
        mode = leg["mode"]
        money[mode] = money.get(mode, 0.0) + float(leg["cost_per_tonne"])
        if mode != previous:
            handlings[mode] = handlings.get(mode, 0) + 1
        previous = mode
    inputs = hauled.get("inputs") or {}
    return Haul(float(hauled["days"]), tuple(sorted(money.items())), tuple(sorted(handlings.items())),
                tuple(sorted((inputs.get("km_by_mode") or {}).items())),
                tuple(sorted((inputs.get("team_days") or {}).items())))


class CarriageTable:
    """Cheapest money cost per tonne between tiles over geography's route graph.

    Costs from a source tile are computed on first use and cached; `warm()` fills every source.
    `world_map` is geography's map (the base map when None); `held_nodes` are the tech nodes the
    society holds, which open-sea lanes may require; `improvements` is the built roads and track,
    `{edge_key: {"road": true}}`, which only a mode with a rate here can use."""

    def __init__(self, tile_ids: Iterable[TileId], money_per_tonne_km_by_mode: Mapping[str, float],
                 handling_money_per_tonne_by_mode: Optional[Mapping[str, float]] = None,
                 held_nodes: Iterable[str] = (), world_map=None,
                 improvements: Optional[Mapping[str, Mapping[str, object]]] = None):
        self.tile_ids = tuple(sorted(tile_ids))
        self._tile_set = frozenset(self.tile_ids)
        self._rates = dict(money_per_tonne_km_by_mode)
        self._handling = dict(handling_money_per_tonne_by_mode or {})
        self._held_nodes = tuple(sorted(held_nodes))
        self._world_map = world_map
        self._improvements = dict(improvements or {})
        self._from_source: Dict[TileId, Dict[TileId, float]] = {}
        self._warmed = False    # whether the whole table has been filled (or fetched) already
        self.scale = 1.0        # multiplier on every cost: the year's wage on the labour part of the rates (set_scale)
        self._scaled: Dict[TileId, Dict[TileId, float]] = {}
        self._hauls: Dict[tuple, Haul] = {}

    def set_scale(self, scale: float) -> None:
        """Multiply every cost by `scale` (1: the costs as searched, the very same answers)."""
        if scale != self.scale:
            self.scale = scale
            self._scaled = {}

    def costs_from(self, source: TileId) -> Dict[TileId, float]:
        """Cheapest cost to every given tile reachable from `source` (unreachable tiles are absent)."""
        found = self._searched_costs_from(source)
        if self.scale == 1.0:
            return found
        scaled = self._scaled.get(source)
        if scaled is None:
            scaled = self._scaled[source] = {tile: cost * self.scale for tile, cost in found.items()}
        return scaled

    def _searched_costs_from(self, source: TileId) -> Dict[TileId, float]:
        cached = self._from_source.get(source)
        if cached is None and not self._warmed:
            self.warm(remember=True)
            cached = self._from_source.get(source)
        if cached is None:
            cached = self._search(source)
            self._from_source[source] = cached
        return cached

    def _search(self, source: TileId) -> Dict[TileId, float]:
        everywhere = route_costs(
            [source], sorted(self._rates), mode_costs=self._rates, handling_costs=self._handling,
            held_nodes=self._held_nodes, world_map=self._world_map,
            improvements=self._improvements, within=self._tile_set)
        return {tile_id: cost for tile_id, cost in everywhere.items() if tile_id in self._tile_set}

    def cost_per_tonne(self, from_tile: TileId, to_tile: TileId) -> float:
        """Money per tonne by the cheapest path; infinite when no path exists."""
        return self.costs_from(from_tile).get(to_tile, math.inf)

    def days_between(self, from_tile: TileId, to_tile: TileId) -> float:
        """Days a haul takes by the cheapest path (geography's pace for each leg's mode, handling included);
        infinite when no path exists."""
        return self.haul(from_tile, to_tile).days

    def haul(self, from_tile: TileId, to_tile: TileId) -> Haul:
        """The cheapest path between two tiles as modes, kilometres and handlings (kept: one route search a
        pair); `NO_PATH` when none joins them."""
        key = (from_tile, to_tile)
        found = self._hauls.get(key)
        if found is None:
            hauled = route([from_tile], [to_tile], sorted(self._rates), self._improvements, self._rates,
                           self._handling, self._held_nodes, self._world_map)
            found = self._hauls[key] = NO_PATH if hauled is None else haul_of(hauled)
        return found

    def unscaled_cost_per_tonne(self, from_tile: TileId, to_tile: TileId) -> float:
        """`cost_per_tonne` before the year's wage scale."""
        return self._searched_costs_from(from_tile).get(to_tile, math.inf)

    def warm(self, remember: bool = False) -> None:
        """Fill every source. With `remember` the whole table is read from disk when an earlier process
        searched the same inputs, and stored there after a search."""
        self._warmed = True
        if remember:
            key = carriage_cache.table_key(self._world_map if self._world_map is not None else open_map(), {
                "tiles": self.tile_ids, "rates": self._rates, "handling": self._handling,
                "held": self._held_nodes, "ways": self._improvements})
            table = carriage_cache.read(key)
            if table is not None and set(table) == self._tile_set:
                self._from_source.update(table)
                return
        for tile_id in self.tile_ids:
            self.costs_from(tile_id)
        if remember:
            carriage_cache.write(key, self._from_source)


def carriage_table(tiles: Mapping[TileId, TileSpec], money_per_tonne_km_by_mode: Mapping[str, float],
                   handling_money_per_tonne_by_mode: Optional[Mapping[str, float]] = None,
                   held_nodes: Iterable[str] = (), world_map=None,
                   improvements: Optional[Mapping[str, Mapping[str, object]]] = None) -> CarriageTable:
    """A table over these tiles at the given rates, with the built ways."""
    return CarriageTable(tiles, money_per_tonne_km_by_mode, handling_money_per_tonne_by_mode, held_nodes, world_map,
                         improvements)
