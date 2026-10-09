"""The edges between tiles that carriage modes run over: land, river, coast and open sea.

Land edges join bordering tiles (km is the great circle between centres times a detour); a land
edge carries a grade from the tile layers (`elevation_std_m`, else `ruggedness_index`, plus the
slope between `elevation_mean_m` values), else a labelled default. River edges join bordering
tiles that both have `river_km_navigable` above a threshold or share a `river_id`; the current runs
toward the lower `elevation_mean_m`. Sea edges come from the map's `sea_links` catalogue when it has one
(water paths over a rasterised ocean: km is the water distance, the class is `coast` while the path stays
within the offshore limit of a coast, else `open_sea`, and the lane boxes use the path midpoint); a map
without the catalogue joins coastal tiles within range whose chord does not cross another tile's land,
a chord up to the coast range being `coast`, a longer one `open_sea`. A sea leg may need tech nodes by a
sea lane. Coefficients are map parameters (`parameters/routes.json`).

An edge key is the sorted "tile_a|tile_b" string callers use for improvements. Built once per map.

Standalone: reads the map, imports nothing outside this package.
"""
import math
from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Tuple

from sim.geography import parameters, routes_modes, tile_layers, transport
from sim.geography.distance import haversine_km
from sim.geography.map_source import WorldMap


@dataclass(frozen=True)
class Edge:
    """One undirected edge. `current_km_per_hour` is signed from tile_a to tile_b (river only; 0 when
    the flow direction is unknown). `lane_nodes` are the nodes an open-sea leg needs. `crosses_river`
    marks a land edge between tiles on the same river, which a land carrier fords unless it is bridged."""
    tile_a: str
    tile_b: str
    edge_class: str
    km: float
    grade: float = 0.0
    current_km_per_hour: float = 0.0
    lane_nodes: FrozenSet[str] = frozenset()
    crosses_river: bool = False

    @property
    def key(self) -> str:
        return edge_key(self.tile_a, self.tile_b)


@dataclass
class RouteGraph:
    tile_ids: Tuple[str, ...]
    edges: Tuple[Edge, ...]
    coordinates: Dict[str, Tuple[float, float]]
    compiled: Dict[object, object]


def edge_key(tile_a: str, tile_b: str) -> str:
    """The sorted key of the edge between two tiles, as used in an improvements dict."""
    return "%s|%s" % (tile_a, tile_b) if tile_a <= tile_b else "%s|%s" % (tile_b, tile_a)


def _tile_roughness(world_map: WorldMap, tile_id: str) -> Optional[float]:
    deviation = tile_layers.number(world_map, tile_id, "elevation_std_m")
    if deviation is not None:
        return deviation * parameters.parameter(world_map, "route_grade_per_elevation_std_m")
    index = tile_layers.number(world_map, tile_id, "ruggedness_index")
    if index is not None:
        return index * parameters.parameter(world_map, "route_grade_per_ruggedness_m")
    return None


def _land_grade(world_map: WorldMap, tile_a: str, tile_b: str, km: float) -> float:
    found = [roughness for roughness in (_tile_roughness(world_map, tile_a), _tile_roughness(world_map, tile_b))
             if roughness is not None]
    grade = sum(found) / len(found) if found else parameters.parameter(world_map, "route_default_grade")
    height_a = tile_layers.number(world_map, tile_a, "elevation_mean_m")
    height_b = tile_layers.number(world_map, tile_b, "elevation_mean_m")
    if height_a is not None and height_b is not None:
        grade += abs(height_a - height_b) / (km * 1000.0)
    return min(grade, parameters.parameter(world_map, "route_grade_cap"))


def _on_the_same_river(world_map: WorldMap, tile_a: str, tile_b: str) -> bool:
    threshold = parameters.parameter(world_map, "route_river_navigable_km_threshold")
    if all((tile_layers.number(world_map, tile, "river_km_navigable") or 0.0) >= threshold
           for tile in (tile_a, tile_b)):
        return True
    river = tile_layers.value(world_map, tile_a, "river_id")
    return river is not None and river == tile_layers.value(world_map, tile_b, "river_id")


def _river_current(world_map: WorldMap, tile_a: str, tile_b: str) -> float:
    """Signed km per hour from tile_a to tile_b; 0 when the layers do not say which way water runs."""
    height_a = tile_layers.number(world_map, tile_a, "elevation_mean_m")
    height_b = tile_layers.number(world_map, tile_b, "elevation_mean_m")
    if height_a is None or height_b is None or height_a == height_b:
        return 0.0
    speeds = [tile_layers.number(world_map, tile, "river_current_km_per_hour")
              for tile in (tile_a, tile_b)]
    speeds = [speed for speed in speeds if speed is not None]
    speed = sum(speeds) / len(speeds) if speeds else transport.TYPICAL_NAVIGABLE_RIVER_CURRENT_KM_PER_HOUR
    return speed if height_a > height_b else -speed


def _land_and_river_edges(world_map: WorldMap, coordinates) -> List[Edge]:
    detour = parameters.parameter(world_map, "route_land_detour_factor")
    river_detour = parameters.parameter(world_map, "route_river_detour_factor")
    pairs = set()
    for tile_id, tile in world_map.tiles.items():
        for other in tile.get("borders", ()):
            if other in world_map.tiles and other != tile_id:
                pairs.add((tile_id, other) if tile_id < other else (other, tile_id))
    edges = []
    for tile_a, tile_b in sorted(pairs):
        centre_km = haversine_km(*coordinates[tile_a], *coordinates[tile_b])
        km = centre_km * detour
        on_river = _on_the_same_river(world_map, tile_a, tile_b)
        edges.append(Edge(tile_a, tile_b, "land", km, _land_grade(world_map, tile_a, tile_b, km), crosses_river=on_river))
        if on_river:
            edges.append(Edge(tile_a, tile_b, "river", centre_km * river_detour,
                              current_km_per_hour=_river_current(world_map, tile_a, tile_b)))
    return edges


def _unit_vector(latitude: float, longitude: float) -> Tuple[float, float, float]:
    phi, lam = math.radians(latitude), math.radians(longitude)
    return (math.cos(phi) * math.cos(lam), math.cos(phi) * math.sin(lam), math.sin(phi))


class _LandCells:
    """Which tile centres lie near a point, by a grid on the unit sphere."""

    def __init__(self, coordinates, clearance_km: float):
        self.cell = clearance_km / 6371.0
        self.reach = self.cell * self.cell
        self.grid: Dict[Tuple[int, int, int], List[Tuple[str, Tuple[float, float, float]]]] = {}
        for tile_id, (latitude, longitude) in coordinates.items():
            vector = _unit_vector(latitude, longitude)
            self.grid.setdefault(self._cell_of(vector), []).append((tile_id, vector))

    def _cell_of(self, vector):
        return (math.floor(vector[0] / self.cell), math.floor(vector[1] / self.cell),
                math.floor(vector[2] / self.cell))

    def near(self, vector, ignore) -> bool:
        cx, cy, cz = self._cell_of(vector)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for tile_id, other in self.grid.get((cx + dx, cy + dy, cz + dz), ()):
                        if tile_id in ignore:
                            continue
                        squared = sum((vector[axis] - other[axis]) ** 2 for axis in range(3))
                        if squared < self.reach:
                            return True
        return False


def _chord_points(start, end, count):
    """`count` interior points along the great circle from start to end (unit vectors)."""
    dot = max(-1.0, min(1.0, sum(start[axis] * end[axis] for axis in range(3))))
    angle = math.acos(dot)
    if angle == 0.0:
        return []
    points = []
    for step in range(1, count + 1):
        along = step / (count + 1)
        weight_a, weight_b = math.sin((1 - along) * angle) / math.sin(angle), math.sin(along * angle) / math.sin(angle)
        points.append(tuple(weight_a * start[axis] + weight_b * end[axis] for axis in range(3)))
    return points


def _midpoint(coordinates, tile_a, tile_b) -> Tuple[float, float]:
    vector_a, vector_b = _unit_vector(*coordinates[tile_a]), _unit_vector(*coordinates[tile_b])
    middle = [vector_a[axis] + vector_b[axis] for axis in range(3)]
    return (math.degrees(math.atan2(middle[2], math.hypot(middle[0], middle[1]))),
            math.degrees(math.atan2(middle[1], middle[0])))


def _catalogue_sea_edges(world_map: WorldMap) -> List[Edge]:
    offshore_limit = parameters.parameter(world_map, "route_coast_offshore_max_km")
    edges = []
    for _link_id, link in sorted(world_map.catalogue("sea_links").items()):
        tile_a, tile_b = link["tile_a"], link["tile_b"]
        if tile_a not in world_map.tiles or tile_b not in world_map.tiles:
            continue
        edge_class = "coast" if link["max_offshore_km"] <= offshore_limit else "open_sea"
        lane_nodes = routes_modes.lane_requirements(world_map, link["midpoint_lat"], link["midpoint_lon"], edge_class)
        edges.append(Edge(tile_a, tile_b, edge_class, float(link["water_km"]), lane_nodes=lane_nodes))
    return edges


def _sea_edges(world_map: WorldMap, coordinates) -> List[Edge]:
    if world_map.catalogue("sea_links"):
        return _catalogue_sea_edges(world_map)
    coast_range = parameters.parameter(world_map, "route_coast_link_range_km")
    open_range = parameters.parameter(world_map, "route_open_sea_link_range_km")
    coast_detour = parameters.parameter(world_map, "route_coast_detour_factor")
    open_detour = parameters.parameter(world_map, "route_open_sea_detour_factor")
    clearance = parameters.parameter(world_map, "route_sea_chord_land_clearance_km")
    land = _LandCells(coordinates, clearance)
    has_port_layer = "is_port" in world_map.layers
    coastal = sorted(tile_id for tile_id, tile in world_map.tiles.items() if tile.get("coastal")
                     and (not has_port_layer or tile_layers.value(world_map, tile_id, "is_port")))
    edges = []
    for index, tile_a in enumerate(coastal):
        for tile_b in coastal[index + 1:]:
            if abs(coordinates[tile_a][0] - coordinates[tile_b][0]) * 111.0 > open_range:
                continue
            distance = haversine_km(*coordinates[tile_a], *coordinates[tile_b])
            if distance > open_range:
                continue
            samples = int(distance / clearance)
            ends = {tile_a, tile_b}
            if any(land.near(point, ends) for point in _chord_points(
                    _unit_vector(*coordinates[tile_a]), _unit_vector(*coordinates[tile_b]), samples)):
                continue
            edge_class = "coast" if distance <= coast_range else "open_sea"
            lane_nodes = routes_modes.lane_requirements(world_map, *_midpoint(coordinates, tile_a, tile_b), edge_class)
            edges.append(Edge(tile_a, tile_b, edge_class,
                              distance * (coast_detour if edge_class == "coast" else open_detour), lane_nodes=lane_nodes))
    return edges


def graph(world_map: WorldMap) -> RouteGraph:
    """The map's route graph, built on first use and kept on the map."""
    cached = world_map.__dict__.get("_route_graph")
    if cached is None:
        coordinates = {tile_id: (tile["lat"], tile["lon"]) for tile_id, tile in world_map.tiles.items()}
        edges = _land_and_river_edges(world_map, coordinates) + _sea_edges(world_map, coordinates)
        cached = RouteGraph(tuple(sorted(world_map.tiles)), tuple(edges), coordinates, {})
        world_map.__dict__["_route_graph"] = cached
    return cached


def land_edge(world_map: WorldMap, tile_a: str, tile_b: str) -> Optional[Edge]:
    """The land edge joining two tiles, or None when they do not border (or one is not on the map)."""
    key = edge_key(tile_a, tile_b)
    return next((edge for edge in graph(world_map).edges if edge.edge_class == "land" and edge.key == key), None)


def harbour_edges(world_map: WorldMap, improvements) -> List[Edge]:
    """Sea edges a built port opens: a port tile shares the water of the bordering tiles that have a
    harbour, so it takes their sea edges (the shortest where two reach the same tile). A port is
    recorded under its tile id in `improvements`."""
    ports = sorted(tile_id for tile_id, built in (improvements or {}).items()
                   if tile_id in world_map.tiles and built.get("port"))
    if not ports:
        return []
    by_tile: Dict[str, List[Edge]] = {}
    for edge in graph(world_map).edges:
        if edge.edge_class in ("coast", "open_sea"):
            by_tile.setdefault(edge.tile_a, []).append(edge)
            by_tile.setdefault(edge.tile_b, []).append(edge)
    found: Dict[Tuple[str, str], Edge] = {}
    for port in ports:
        for neighbour in world_map.tiles[port].get("borders", ()):
            for edge in by_tile.get(neighbour, ()):
                other = edge.tile_b if edge.tile_a == neighbour else edge.tile_a
                if other == port:
                    continue
                kept = found.get((port, other))
                if kept is None or edge.km < kept.km:
                    found[(port, other)] = Edge(port, other, edge.edge_class, edge.km, lane_nodes=edge.lane_nodes)
    return [found[pair] for pair in sorted(found)]


def links(world_map: WorldMap, mode_ids) -> List[Tuple[str, str, str, float]]:
    """(tile_a, tile_b, mode, km) for each edge a mode in `mode_ids` runs on without anything built."""
    chosen = routes_modes.modes(world_map)
    result = []
    for edge in graph(world_map).edges:
        for mode_id in sorted(mode_ids):
            mode = chosen[mode_id]
            if edge.edge_class in mode["edge_classes"] and not mode.get("needs_improvement"):
                result.append((edge.tile_a, edge.tile_b, mode_id, edge.km))
    return result
