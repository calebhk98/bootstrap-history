"""What it costs to move a tonne between tiles: a graph of land and sea links, and cheapest paths over it.

Space is tiles (150,000 km2 cells). Land links join bordering tiles; sea links join coastal tiles
within sailing range of each other. The money per tonne-km of each carriage mode is computed by the
caller at current prices (`money_per_tonne_km_by_mode`), so the table follows prices. No river data
exists on tiles: `Link` is the hook for rivers (and canals, roads) once a source names them.

Standalone: `sim.world` freight models, `sim.constants` and `sim.economy.types` only.
"""
import heapq
import math
from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Optional, Tuple

from sim.constants import declare
from sim.economy.types import TileId, TileSpec
from sim.geography.api import freight_cost, sea_freight, transport

DRAUGHT_MODE = "draught"
PACK_MODE = "pack"
SEA_MODE = "sea"
RIVER_MODE = "river"
LAND_MODES = (DRAUGHT_MODE, PACK_MODE)

EARTH_RADIUS_KM = declare(
    "EARTH_RADIUS_KM", 6371.0, kind="physical_constant", unit="km", source="Mean radius.",
    confidence="A", why="Converts the angle between two tile centres into a distance.")
LAND_ROUTE_DETOUR_FACTOR = declare(
    "LAND_ROUTE_DETOUR_FACTOR", 1.3, kind="temporary_heuristic", unit="route km per great-circle km",
    source=None, confidence="D",
    why="Roads wind around hills, rivers and marsh; the factor is not yet derived from relief or a "
        "road network, which tiles do not carry.")
SEA_ROUTE_DETOUR_FACTOR = declare(
    "SEA_ROUTE_DETOUR_FACTOR", 1.3, kind="temporary_heuristic", unit="sailed km per great-circle km",
    source=None, confidence="D",
    why="Coastal shipping follows the shore and puts in at headlands; tiles carry no coastline, so "
        "the detour is a flat factor until a coast model derives it.")
SEA_LINK_RANGE_KM = declare(
    "SEA_LINK_RANGE_KM", 900.0, kind="temporary_heuristic", unit="great-circle km",
    source=None, confidence="D",
    why="Two coastal tiles within this range count as one sailing leg apart; longer voyages chain "
        "legs and pay each leg's port handling. The great circle may cross land (a link between "
        "two seas), which tile data cannot rule out; replace with sea-lane data when it exists.")
PACK_STRING_SIZE = declare(
    "PACK_STRING_SIZE", 5, kind="engineering_estimate", unit="pack animals per handler",
    source="A muleteer drove a string of several animals.", confidence="D",
    why="Spreads the handler's day over the string's cargo in the pack-mode freight rate.")
DRAUGHT_TEAM_SIZE = declare(
    "DRAUGHT_TEAM_SIZE", 2, kind="engineering_estimate", unit="oxen per cart",
    source="sim/world/transport.py uses a two-ox cart as its ordinary draught case.", confidence="C",
    why="The cart team whose freight rate prices overland carriage between tiles.")


@dataclass(frozen=True)
class Link:
    """A carriage link outside the land and sea rules (a river, a canal, a paved road)."""
    tile_a: TileId
    tile_b: TileId
    mode: str
    distance_km: float


@dataclass(frozen=True)
class Edge:
    """One undirected link: it may be carried by any of `modes`; the cheapest at current rates wins."""
    tile_a: TileId
    tile_b: TileId
    modes: Tuple[str, ...]
    distance_km: float


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
            fertility=record["fertility_quality_multiplier"])
    return result


def great_circle_km(latitude_a: float, longitude_a: float, latitude_b: float, longitude_b: float) -> float:
    phi_a, phi_b = math.radians(latitude_a), math.radians(latitude_b)
    half_delta_phi = (phi_b - phi_a) / 2.0
    half_delta_lambda = math.radians(longitude_b - longitude_a) / 2.0
    haversine = (math.sin(half_delta_phi) ** 2
                 + math.cos(phi_a) * math.cos(phi_b) * math.sin(half_delta_lambda) ** 2)
    return 2.0 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(haversine)))


def tile_distance_km(tile_a: TileSpec, tile_b: TileSpec) -> float:
    return great_circle_km(tile_a.latitude, tile_a.longitude, tile_b.latitude, tile_b.longitude)


def neighbour_graph(tiles: Mapping[TileId, TileSpec]) -> Dict[TileId, Tuple[TileId, ...]]:
    """Bordering tiles within the given set, made symmetric (a border listed on one side counts)."""
    neighbours = {tile_id: set() for tile_id in tiles}
    for tile_id, tile in tiles.items():
        for other in tile.borders:
            if other in tiles and other != tile_id:
                neighbours[tile_id].add(other)
                neighbours[other].add(tile_id)
    return {tile_id: tuple(sorted(others)) for tile_id, others in neighbours.items()}


def build_edges(tiles: Mapping[TileId, TileSpec], extra_links: Iterable[Link] = ()) -> Tuple[Edge, ...]:
    """The price-independent geometry: land edges between neighbours, sea edges between coastal tiles
    in range, and any supplied links. Build once; reuse across price changes."""
    edges: List[Edge] = []
    for tile_id, others in neighbour_graph(tiles).items():
        for other in others:
            if tile_id < other:
                distance = tile_distance_km(tiles[tile_id], tiles[other]) * LAND_ROUTE_DETOUR_FACTOR
                edges.append(Edge(tile_id, other, LAND_MODES, distance))
    coastal = sorted(tile_id for tile_id, tile in tiles.items() if tile.coastal)
    for index, tile_id in enumerate(coastal):
        for other in coastal[index + 1:]:
            distance = tile_distance_km(tiles[tile_id], tiles[other])
            if distance <= SEA_LINK_RANGE_KM:
                edges.append(Edge(tile_id, other, (SEA_MODE,), distance * SEA_ROUTE_DETOUR_FACTOR))
    for link in extra_links:
        if link.tile_a in tiles and link.tile_b in tiles:
            edges.append(Edge(link.tile_a, link.tile_b, (link.mode,), link.distance_km))
    return tuple(edges)


class CarriageTable:
    """Cheapest money cost per tonne between tiles over the mixed land and sea graph.

    Costs from a source tile are computed on first use and cached; `warm()` fills every source."""

    def __init__(self, tile_ids: Iterable[TileId], edges: Iterable[Edge],
                 money_per_tonne_km_by_mode: Mapping[str, float],
                 handling_money_per_tonne_by_mode: Optional[Mapping[str, float]] = None):
        handling = handling_money_per_tonne_by_mode or {}
        self.tile_ids = tuple(sorted(tile_ids))
        self._adjacency: Dict[TileId, List[Tuple[TileId, float]]] = {tile_id: [] for tile_id in self.tile_ids}
        for edge in edges:
            costs = [edge.distance_km * money_per_tonne_km_by_mode[mode] + handling.get(mode, 0.0)
                     for mode in edge.modes if mode in money_per_tonne_km_by_mode]
            if costs:
                cheapest = min(costs)
                self._adjacency[edge.tile_a].append((edge.tile_b, cheapest))
                self._adjacency[edge.tile_b].append((edge.tile_a, cheapest))
        self._from_source: Dict[TileId, Dict[TileId, float]] = {}

    def costs_from(self, source: TileId) -> Dict[TileId, float]:
        """Cheapest cost to every tile reachable from `source` (unreachable tiles are absent)."""
        cached = self._from_source.get(source)
        if cached is not None:
            return cached
        best = {source: 0.0}
        settled = set()
        queue = [(0.0, source)]
        while queue:
            cost, tile_id = heapq.heappop(queue)
            if tile_id in settled:
                continue
            settled.add(tile_id)
            for other, edge_cost in self._adjacency[tile_id]:
                candidate = cost + edge_cost
                if candidate < best.get(other, math.inf):
                    best[other] = candidate
                    heapq.heappush(queue, (candidate, other))
        self._from_source[source] = best
        return best

    def cost_per_tonne(self, from_tile: TileId, to_tile: TileId) -> float:
        """Money per tonne by the cheapest path; infinite when no path exists."""
        return self.costs_from(from_tile).get(to_tile, math.inf)

    def warm(self) -> None:
        for tile_id in self.tile_ids:
            self.costs_from(tile_id)


def carriage_table(tiles: Mapping[TileId, TileSpec], money_per_tonne_km_by_mode: Mapping[str, float],
                   handling_money_per_tonne_by_mode: Optional[Mapping[str, float]] = None,
                   edges: Optional[Iterable[Edge]] = None) -> CarriageTable:
    """A table at the given rates. Pass `edges` from `build_edges` to skip rebuilding the geometry."""
    return CarriageTable(tiles, build_edges(tiles) if edges is None else edges,
                         money_per_tonne_km_by_mode, handling_money_per_tonne_by_mode)


def money_per_tonne_km_by_mode(carrier_prices: Mapping[str, freight_cost.CarrierPrices],
                               wage_per_hour: float, feed_price_per_kg: float, annual_rate: float,
                               imbalance: float = 1.0) -> Dict[str, float]:
    """Money per loaded tonne-km for each mode named in `carrier_prices` (DRAUGHT_MODE, PACK_MODE,
    SEA_MODE): the carrier unit's money price (cart and team, saddles and string, hull) at today's
    prices. Crew rations at sea are priced at `feed_price_per_kg`. Rivers have no tile data yet."""
    rates = {}
    if DRAUGHT_MODE in carrier_prices:
        inputs = transport.draught_freight_physical_inputs(
            transport.OX, DRAUGHT_TEAM_SIZE, transport.CART, transport.DIRT_TRACK)
        rates[DRAUGHT_MODE] = freight_cost.freight_money_per_tonne_km(
            inputs, feed_price_per_kg, wage_per_hour, carrier_prices[DRAUGHT_MODE], annual_rate,
            freight_cost.LAND_WORKING_DAYS_PER_YEAR, imbalance)
    if PACK_MODE in carrier_prices:
        inputs = transport.pack_freight_physical_inputs(transport.MULE, PACK_STRING_SIZE)
        rates[PACK_MODE] = freight_cost.freight_money_per_tonne_km(
            inputs, feed_price_per_kg, wage_per_hour, carrier_prices[PACK_MODE], annual_rate,
            freight_cost.LAND_WORKING_DAYS_PER_YEAR, imbalance)
    if SEA_MODE in carrier_prices:
        inputs = sea_freight.sailing_freight_physical_inputs()
        rates[SEA_MODE] = freight_cost.freight_money_per_tonne_km(
            inputs, feed_price_per_kg, wage_per_hour, carrier_prices[SEA_MODE], annual_rate,
            sea_freight.SAILING_DAYS_PER_YEAR, imbalance, freight_cost.HULL_LOSS_PER_THOUSAND_KM)
    return rates


def handling_money_per_tonne_by_mode(wage_per_hour: float) -> Dict[str, float]:
    """Port handling per tonne per sea leg (loading and unloading), at the going wage."""
    return {SEA_MODE: sea_freight.PORT_HANDLING_HOURS_PER_TONNE * wage_per_hour}
