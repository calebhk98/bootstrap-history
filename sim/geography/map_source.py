"""A map: tiles, per-tile layers and content catalogues, merged from an ordered list of folders.

The first folder is the base map (`data/world/geography/`); each later folder is an overlay owned
by a mod and follows the mod rules in mods/README.md: a new id is `<mod_id>:<name>`, an entry
with `"override": true` deep-merges into an existing id, `"remove": true` deletes one, and a
`null` inside an override deletes that key. Layout of a folder:

    map.json                      {"id", "tiles": {"file", "path"}} (base, or an overlay replacing tiles)
    tiles/*.json                  {"entries": [{"id", ...tile fields}]} new tiles or tile patches
    layers/*.json                 {"id", "unit", "source", "values": {tile_id: value}}
    <catalogue>/*.json            {"entries": [{"id", ...}]} any other subfolder is a catalogue

Standalone: reads files, imports nothing outside this package.
"""
import copy
import functools
import json
import os
from typing import Any, Dict, Iterable, List, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_MAP_FOLDER = os.path.join(ROOT, "data", "world", "geography")
RESERVED_FOLDERS = ("tiles", "layers")


class MapDataError(ValueError):
    """A map folder that cannot be merged; the message names the file."""


class WorldMap:
    """One merged map. Read-only by convention: callers get copies of nothing, so do not mutate."""

    def __init__(self, map_id: str, tiles: Dict[str, Dict[str, Any]],
                 layers: Dict[str, Dict[str, Any]], catalogues: Dict[str, Dict[str, Dict[str, Any]]],
                 folders: Tuple[str, ...], properties: Optional[Dict[str, Any]] = None):
        self.map_id = map_id
        self.properties = properties or {}  # scalar facts stated beside the tiles, such as their nominal area
        self.tiles = tiles
        self.layers = layers
        self.catalogues = catalogues
        self.folders = folders

    def catalogue(self, name: str) -> Dict[str, Dict[str, Any]]:
        """{entry_id: entry} of one catalogue (empty when the map has none)."""
        return self.catalogues.get(name, {})


def _read_json(path: str) -> Any:
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError) as error:
        raise MapDataError("%s: %s" % (path, error)) from error


def _json_files(folder: str) -> List[str]:
    if not os.path.isdir(folder):
        return []
    return [os.path.join(folder, name) for name in sorted(os.listdir(folder)) if name.endswith(".json")]


def _entries(path: str) -> List[Dict[str, Any]]:
    content = _read_json(path)
    entries = content.get("entries") if isinstance(content, dict) else content
    if not isinstance(entries, list):
        raise MapDataError("%s: expected a list of entries or {\"entries\": [...]}" % path)
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
            raise MapDataError("%s: every entry needs a string id" % path)
    return entries


def deep_merge(target: Dict[str, Any], patch: Dict[str, Any]) -> Dict[str, Any]:
    """`patch` merged into a copy of `target`: nested dicts merge, `None` deletes a key."""
    merged = copy.deepcopy(target)
    for key, value in patch.items():
        if value is None:
            merged.pop(key, None)
        elif isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def _apply_entry(items: Dict[str, Dict[str, Any]], entry: Dict[str, Any], owner: Optional[str],
                 path: str) -> None:
    """Add, patch or remove one entry under the mod rules."""
    entry_id = entry["id"]
    body = {key: value for key, value in entry.items() if key not in ("override", "remove")}
    if entry.get("remove"):
        if entry_id not in items:
            raise MapDataError("%s: cannot remove %r, no such entry" % (path, entry_id))
        del items[entry_id]
    elif entry.get("override"):
        if entry_id not in items:
            raise MapDataError("%s: cannot override %r, no such entry" % (path, entry_id))
        items[entry_id] = deep_merge(items[entry_id], body)
    else:
        if owner is not None and not entry_id.startswith(owner + ":"):
            raise MapDataError("%s: new id %r must be named %s:<name>" % (path, entry_id, owner))
        if entry_id in items:
            raise MapDataError("%s: %r already exists; mark it \"override\": true to patch it"
                               % (path, entry_id))
        items[entry_id] = body


def _load_tiles(folder: str, manifest: Dict[str, Any]) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
    """(tiles, the scalar values stored beside them) from the file the manifest names."""
    source = manifest["tiles"]
    container = _read_json(os.path.normpath(os.path.join(folder, source["file"])))
    content = container
    for key in source.get("path", []):
        container, content = content, content[key]
    properties = {key: value for key, value in container.items()
                  if content is not container and isinstance(value, (int, float, str)) and not key.startswith("_")}
    properties.update(manifest.get("properties", {}))
    return {tile_id: dict(record, id=tile_id) for tile_id, record in content.items()}, properties


def _merge_layer(layers: Dict[str, Dict[str, Any]], layer: Dict[str, Any], owner: Optional[str],
                 path: str) -> None:
    """A layer file adds a layer, or with `"override": true` patches values of an existing one."""
    layer_id = layer.get("id")
    if not isinstance(layer_id, str) or not isinstance(layer.get("values"), dict):
        raise MapDataError("%s: a layer needs a string id and a values map" % path)
    if layer.get("override"):
        if layer_id not in layers:
            raise MapDataError("%s: cannot override layer %r, no such layer" % (path, layer_id))
        merged = deep_merge(layers[layer_id], {key: value for key, value in layer.items()
                                               if key not in ("override", "values")})
        merged["values"] = deep_merge(layers[layer_id]["values"], layer["values"])
        layers[layer_id] = merged
        return
    if owner is not None and not layer_id.startswith(owner + ":"):
        raise MapDataError("%s: new layer %r must be named %s:<name>" % (path, layer_id, owner))
    if layer_id in layers:
        raise MapDataError("%s: layer %r already exists" % (path, layer_id))
    layers[layer_id] = dict(layer)


def merge_folders(folders: Iterable[Tuple[Optional[str], str]]) -> WorldMap:
    """Merge (owner, folder) pairs in order. The base folder's owner is None; a mod's is its id."""
    folders = tuple(folders)
    if not folders:
        raise MapDataError("a map needs at least one folder")
    map_id, tiles, properties = None, {}, {}
    layers: Dict[str, Dict[str, Any]] = {}
    catalogues: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for owner, folder in folders:
        manifest_path = os.path.join(folder, "map.json")
        if os.path.exists(manifest_path):
            manifest = _read_json(manifest_path)
            if "tiles" in manifest:
                tiles, properties = _load_tiles(folder, manifest)
                map_id = manifest.get("id", map_id)
                if owner is not None:
                    layers = {}  # a replacement map's layers describe other tiles
        elif owner is None:
            raise MapDataError("%s: the base map folder needs a map.json" % folder)
        for path in _json_files(os.path.join(folder, "tiles")):
            for entry in _entries(path):
                _apply_entry(tiles, entry, owner, path)
        for path in _json_files(os.path.join(folder, "layers")):
            _merge_layer(layers, _read_json(path), owner, path)
        for name in sorted(os.listdir(folder)):
            if name in RESERVED_FOLDERS or not os.path.isdir(os.path.join(folder, name)):
                continue
            items = catalogues.setdefault(name, {})
            for path in _json_files(os.path.join(folder, name)):
                for entry in _entries(path):
                    _apply_entry(items, entry, owner, path)
    if map_id is None:
        raise MapDataError("no folder named the map's tiles in its map.json")
    return WorldMap(map_id, tiles, layers, catalogues, tuple(folder for _owner, folder in folders), properties)


def map_of_tiles(tile_records: Dict[str, Dict[str, Any]], like: WorldMap) -> WorldMap:
    """A map of the given tiles that keeps only `like`'s route catalogues and parameters (no layers, no
    sea_links: sea edges are then joined from the tiles' coasts)."""
    kept = {name: like.catalogue(name) for name in ("route_modes", "sea_lanes", "parameters")}
    tiles = {tile_id: dict(record, id=tile_id) for tile_id, record in tile_records.items()}
    return WorldMap("tiles_of_%s" % like.map_id, tiles, {}, kept, ())


def mod_overlay_folders(mods: Iterable[Tuple[str, str]]) -> List[Tuple[str, str]]:
    """(mod_id, folder) for each mod, in the given load order, that ships a map overlay."""
    return [(mod_id, os.path.join(mod_root, "data", "world", "geography"))
            for mod_id, mod_root in mods
            if os.path.isdir(os.path.join(mod_root, "data", "world", "geography"))]


@functools.lru_cache(maxsize=8)
def load_map(overlays: Tuple[Tuple[str, str], ...] = (), base_folder: str = BASE_MAP_FOLDER) -> WorldMap:
    """The base map with `overlays` ((mod_id, mod_root) in load order) merged on top. Cached."""
    return merge_folders(((None, base_folder),) + tuple(mod_overlay_folders(overlays)))
