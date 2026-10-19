"""Declared stores: a named value per tile, per actor or per ordered pair of actors, saved with the game.

A store is declared in data (`data/world/stores.json` for the base game, `data/stores.json` in a mod) or by a
mod's code through `api.store`. A mod's names are `<mod_id>:<name>`; a name is declared once across the base
game and every mod. Only values that differ from the default are kept, in `state.stores` ({name: {key: value}}),
which the save walks like any other state. `sim.stores.<name>.<key>` reads one value, so figures, `read`
commands and the map screen's layers reach a store through the same dotted state path as any other state.
"""
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from sim.json_files import read_json

from .mods import get_ordered_mods
from .mods_base import ModError
from .mods_ids import check_new_id
from .tree_source import ROOT

STORES_FILE = os.path.join("data", "stores.json")
BASE_STORES_FILE = os.path.join("data", "world", "stores.json")
TILE, ACTOR, ACTOR_PAIR = "tile", "actor", "actor_pair"
KEYED_BY = (TILE, ACTOR, ACTOR_PAIR)
PAIR_SEPARATOR = "|"


@dataclass(frozen=True)
class StoreSpec:
    name: str
    owner: str          # the declaring mod's id; empty for the base game
    keyed_by: str
    default: Any
    unit: str


DECLARED: Dict[str, StoreSpec] = {}


def forget_mod_stores() -> None:
    """Drop every declaration but the base game's (a test or a reload starts again)."""
    for name in [name for name, spec in DECLARED.items() if spec.owner]:
        del DECLARED[name]


def declare(spec: StoreSpec, where: str) -> None:
    if spec.keyed_by not in KEYED_BY:
        raise ModError("%s: store %s is keyed_by %r; it must be one of %s" % (where, spec.name, spec.keyed_by, ", ".join(KEYED_BY)))
    try:
        json.dumps(spec.default)
    except TypeError:
        raise ModError("%s: store %s has a default that is not JSON data" % (where, spec.name))
    held = DECLARED.get(spec.name)
    if held is not None:
        if held == spec:
            return
        raise ModError("%s: store %s is already declared by %s" % (where, spec.name, held.owner or "the base game"))
    DECLARED[spec.name] = spec


def _declare_file(path: str, owner: str, manifest: Any) -> None:
    for name, entry in (read_json(path).get("stores") or {}).items():
        if manifest is not None:
            check_new_id(manifest, name, False, path)
        if not isinstance(entry, dict) or "default" not in entry:
            raise ModError("%s: store %s needs 'keyed_by', 'default' and 'unit'" % (path, name))
        declare(StoreSpec(name, owner, str(entry.get("keyed_by")), entry["default"], str(entry.get("unit", ""))), path)


def load_base_stores(root: str = ROOT) -> None:
    path = os.path.join(root, BASE_STORES_FILE)
    if os.path.isfile(path):
        _declare_file(path, "", None)


def load_mod_stores(mods_dir: str) -> None:
    """Declare the stores every installed mod lists in its data/stores.json."""
    for manifest in get_ordered_mods(mods_dir):
        path = os.path.join(manifest.directory, STORES_FILE)
        if os.path.isfile(path):
            _declare_file(path, manifest.id, manifest)


def spec_of(name: str, mod_id: str = "") -> StoreSpec:
    spec = DECLARED.get(name)
    if spec is None:
        raise ModError("%sstore %s is not declared" % ("mod %s writes " % mod_id if mod_id else "", name))
    return spec


def store_key(spec: StoreSpec, key: Any) -> str:
    """The saved form of a key: a tile or actor id as is, a pair as `first|second` (order matters)."""
    if spec.keyed_by == ACTOR_PAIR:
        if not (isinstance(key, (tuple, list)) and len(key) == 2) and not (isinstance(key, str) and key.count(PAIR_SEPARATOR) == 1):
            raise ModError("store %s is keyed by an ordered pair of actors, not %r" % (spec.name, key))
        key = PAIR_SEPARATOR.join(key) if not isinstance(key, str) else key
    if not isinstance(key, str) or not key:
        raise ModError("store %s is keyed by %s ids (text), not %r" % (spec.name, spec.keyed_by, key))
    return key


class StoreView:
    """One store's values: `view.get(key)`, or `view.<key>` for a dotted state path."""

    def __init__(self, spec: StoreSpec, values: Dict[str, Any]):
        self.spec, self.values = spec, values

    def get(self, key: Any) -> Any:
        return self.values.get(store_key(self.spec, key), self.spec.default)

    def __getattr__(self, key: str) -> Any:
        if key.startswith("_") or key in ("spec", "values"):
            raise AttributeError(key)
        return self.values.get(key, self.spec.default)

    def items(self) -> List[Tuple[str, Any]]:
        return sorted(self.values.items())

    def set(self, key: Any, value: Any) -> None:
        key = store_key(self.spec, key)
        try:
            json.dumps(value)
        except TypeError:
            raise ModError("store %s holds JSON data; %r is not" % (self.spec.name, value))
        if value == self.spec.default:
            self.values.pop(key, None)
        else:
            self.values[key] = value


class StoreBook:
    """`sim.stores`: every declared store, over `state.stores`."""

    def __init__(self, saved: Dict[str, Dict[str, Any]]):
        self._saved = saved

    def __getattr__(self, name: str) -> StoreView:
        if name.startswith("_"):
            raise AttributeError(name)
        return self.view(name)

    def view(self, name: str) -> StoreView:
        return StoreView(spec_of(name), self._saved.setdefault(name, {}))

    def write(self, name: str, key: Any, value: Any, mod_id: str = "") -> None:
        spec = spec_of(name, mod_id)
        if mod_id and spec.owner != mod_id:
            raise ModError("mod %s writes store %s, which %s declared" % (mod_id, name, spec.owner or "the base game"))
        self.view(name).set(key, value)


class ModStoresMixin:
    @property
    def stores(self) -> StoreBook:
        return StoreBook(self.state.stores)


class ModStore:
    """What `api.store` returns: the mod's handle to one store, used as `handle.get(sim, key)` and `handle.set(sim, key, value)`."""

    def __init__(self, name: str, mod_id: str):
        self.name, self.mod_id = name, mod_id

    def get(self, sim: Any, key: Any) -> Any:
        return sim.stores.view(self.name).get(key)

    def set(self, sim: Any, key: Any, value: Any) -> None:
        sim.stores.write(self.name, key, value, self.mod_id)

    def items(self, sim: Any) -> List[Tuple[str, Any]]:
        return sim.stores.view(self.name).items()


def tile_layer(sim: Any, name: str) -> Optional[StoreView]:
    """The tile-keyed store a map layer shows, or None when it is not a declared tile store."""
    spec = DECLARED.get(name)
    return sim.stores.view(name) if spec is not None and spec.keyed_by == TILE else None


load_base_stores()
