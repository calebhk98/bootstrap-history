"""`sim.stores`: every declared store of a game, read and written over the module's saved values.

`sim.stores.<name>.<key>` reads one value, so figures, `read` commands and the map screen's layers reach a store through the
same dotted state path as any other state."""
import json
from typing import Any, Dict, List, Optional, Tuple

from sim.assembly.api import door_of
from sim.mod_errors import ModError

from .commands import WriteStore
from .rules import TILE, StoreSpec, store_key


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
    """Every declared store of one game, over its saved values ({name: {key: value}})."""

    def __init__(self, declared: Dict[str, StoreSpec], saved: Dict[str, Dict[str, Any]]):
        self._declared = declared
        self._saved = saved

    def __getattr__(self, name: str) -> StoreView:
        if name.startswith("_"):
            raise AttributeError(name)
        return self.view(name)

    def spec_of(self, name: str, mod_id: str = "") -> StoreSpec:
        spec = self._declared.get(name)
        if spec is None:
            raise ModError("%sstore %s is not declared" % ("mod %s writes " % mod_id if mod_id else "", name))
        return spec

    def declared(self) -> Dict[str, StoreSpec]:
        return dict(self._declared)

    def view(self, name: str) -> StoreView:
        return StoreView(self.spec_of(name), self._saved.setdefault(name, {}))

    def write(self, name: str, key: Any, value: Any, mod_id: str = "") -> None:
        spec = self.spec_of(name, mod_id)
        if mod_id and spec.owner != mod_id:
            raise ModError("mod %s writes store %s, which %s declared" % (mod_id, name, spec.owner or "the base game"))
        self.view(name).set(key, value)

    def tile_layer(self, name: str) -> Optional[StoreView]:
        """The tile-keyed store a map layer shows, or None when it is not a declared tile store."""
        spec = self._declared.get(name)
        return self.view(name) if spec is not None and spec.keyed_by == TILE else None


class ModStore:
    """What `api.store` returns: the mod's handle to one store, used as `handle.get(access, key)` and `handle.set(access, key, value)`;
    `access` is what the mod's code is handed in place of the game."""

    def __init__(self, spec: StoreSpec, mod_id: str):
        self.spec, self.mod_id = spec, mod_id

    @property
    def name(self) -> str:
        return self.spec.name

    def get(self, access: Any, key: Any) -> Any:
        return door_of(access).view("store")[self.name]["values"].get(store_key(self.spec, key), self.spec.default)

    def set(self, access: Any, key: Any, value: Any) -> None:
        door_of(access).send(WriteStore(self.name, key, value, self.mod_id))

    def items(self, access: Any) -> List[Tuple[str, Any]]:
        return sorted(door_of(access).view("store")[self.name]["values"].items())
