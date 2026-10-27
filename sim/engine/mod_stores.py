"""Declared stores, engine side: the declarations the data files make, handed to the stores module (sim/stores/).

A store is declared in data (`data/world/stores.json` for the base game, `data/stores.json` in a mod) or by a mod's code through
`api.store`. The stores module keeps the declarations of one game and their saved values; this file only reads the data files."""
import os
from typing import Any, Dict, List, Optional

from sim.json_files import read_json
from sim.stores.api import TILE, StoreSpec

from .mods import get_ordered_mods
from .mods_base import ModError
from .mods_ids import check_new_id
from .tree_source import ROOT

STORES_FILE = os.path.join("data", "stores.json")
BASE_STORES_FILE = os.path.join("data", "world", "stores.json")


def _specs_in(path: str, owner: str, manifest: Any) -> List[StoreSpec]:
    found = []
    for name, entry in (read_json(path).get("stores") or {}).items():
        if manifest is not None:
            check_new_id(manifest, name, False, path)
        if not isinstance(entry, dict) or "default" not in entry:
            raise ModError("%s: store %s needs 'keyed_by', 'default' and 'unit'" % (path, name))
        found.append(StoreSpec(name, owner, str(entry.get("keyed_by")), entry["default"], str(entry.get("unit", ""))))
    return found


def base_declarations(root: str = ROOT) -> List[StoreSpec]:
    """The stores the base game declares."""
    path = os.path.join(root, BASE_STORES_FILE)
    return _specs_in(path, "", None) if os.path.isfile(path) else []


def data_declarations(mods_dir: str) -> List[StoreSpec]:
    """The stores every installed mod lists in its data/stores.json, in mod load order."""
    found: List[StoreSpec] = []
    for manifest in get_ordered_mods(mods_dir):
        path = os.path.join(manifest.directory, STORES_FILE)
        if os.path.isfile(path):
            found.extend(_specs_in(path, manifest.id, manifest))
    return found


# The base game's stores, for the map screen's list of layers; a game's own stores (a mod's too) are `sim.stores.declared()`.
DECLARED: Dict[str, StoreSpec] = {spec.name: spec for spec in base_declarations()}


def tile_layer(sim: Any, name: str) -> Optional[Any]:
    """The tile-keyed store a map layer shows, or None when it is not a declared tile store."""
    return sim.stores.tile_layer(name)
