"""On-disk memo of a carriage table: the cheapest cost from every source tile, keyed on everything the
searches read (the map's content, the rates, the built ways, the held nodes) and on the source of the
route searches, so a changed input or checkout is a miss, never a stale answer. Optional: an unreadable
entry is a miss and a failed write is ignored.

Standalone: `sim.cache_root` and the standard library.
"""
import hashlib
import json
import os
import tempfile
from typing import Any, Dict, List, Optional, Tuple

from sim import cache_root

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SOURCE_PATHS = ("sim/geography", "sim/economy/tile_costs.py", "sim/constants.py", "sim/unit_conversions.py",
                 "sim/json_files.py")
_KEY_LENGTH = 32

_source_digest: Optional[str] = None
_tables: Dict[str, Dict[str, Dict[str, float]]] = {}    # tables read or searched in this process, by key
_map_digests: List[Tuple[Any, str]] = []    # (map, digest) of maps already hashed, held so an id is not reused


def _python_files(path: str) -> List[str]:
    if os.path.isfile(path):
        return [path]
    found = []
    for directory, subdirectories, filenames in os.walk(path):
        subdirectories[:] = sorted(name for name in subdirectories if name != "__pycache__")
        found += [os.path.join(directory, name) for name in sorted(filenames) if name.endswith(".py")]
    return found


def _source() -> str:
    global _source_digest
    if _source_digest is None:
        digest = hashlib.sha256()
        for relative in _SOURCE_PATHS:
            for path in _python_files(os.path.join(_ROOT, relative)):
                digest.update(os.path.relpath(path, _ROOT).encode("utf-8"))
                with open(path, "rb") as handle:
                    digest.update(handle.read())
        _source_digest = digest.hexdigest()
    return _source_digest


def _map_digest(world_map: Any) -> str:
    for known, digest in _map_digests:
        if known is world_map:
            return digest
    text = json.dumps([world_map.map_id, world_map.properties, world_map.tiles, world_map.layers,
                       world_map.catalogues, list(world_map.folders)], sort_keys=True, default=str)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    _map_digests.append((world_map, digest))
    return digest


def table_key(world_map: Any, inputs: Dict[str, Any]) -> str:
    """The entry name for these search inputs on this map."""
    text = json.dumps({"inputs": inputs, "map": _map_digest(world_map), "source": _source()},
                      sort_keys=True, default=lambda value: sorted(value))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:_KEY_LENGTH]


def _path(key: str) -> str:
    return os.path.join(cache_root.cache_directory("carriage_tables"), key + ".json")


def read(key: str) -> Optional[Dict[str, Dict[str, float]]]:
    if key in _tables:
        return _tables[key]
    try:
        with open(_path(key), encoding="utf-8") as handle:
            _tables[key] = json.load(handle)
    except (OSError, ValueError):
        return None
    return _tables[key]


def write(key: str, table: Dict[str, Dict[str, float]]) -> None:
    _tables[key] = dict(table)
    path = _path(key)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        handle_fd, temporary = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
        with os.fdopen(handle_fd, "w", encoding="utf-8") as handle:
            json.dump(table, handle)
        os.replace(temporary, path)
    except OSError:
        pass
