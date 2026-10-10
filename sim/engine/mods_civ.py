"""Mod civilisations: new files, override patches of any civ, and starting-tech checks."""
import copy
import json
import os
from typing import Any, Dict, Iterable, List, Optional

from .mods_base import ModError, ModManifest, claim_fields, deep_merge, unrelated as _unrelated_claim
from .mods_ids import SEPARATOR, check_new_id
from .mods_remove import TECH, scan_removed

CIVILIZATION = "civilization"
# Patch keys that edit the lists of a civilisation (hazards, starting_techs, notes) item by item.
LIST_OPERATORS = ("append", "remove_items")


def _item_key(item: Any) -> Any:
    """A list item is identified by its `id`, `actor_id` or `name` (first present), else its own value."""
    if not isinstance(item, dict):
        return item
    return next((item[key] for key in ("id", "actor_id", "name") if key in item), None)


def _parent(civ: Dict[str, Any], dotted: str):
    """(the mapping holding the list, the list's key) for a field name such as `cast.seats`; creates no maps."""
    *walk, last = dotted.split(".")
    holder: Any = civ
    for step in walk:
        holder = holder.get(step) if isinstance(holder, dict) else None
    return (holder if isinstance(holder, dict) else {}), last


def apply_list_operators(civ: Dict[str, Any], patch: Dict[str, Any], manifest: ModManifest,
                         by_id: Dict[str, ModManifest], claims: Dict[Any, str], path: str) -> Dict[str, Any]:
    """`append`: {field: [items]} adds to a list field; `remove_items`: {field: [keys]} deletes by key.
    A field may be dotted to reach a list inside a map, for example `cast.seats` or `cast.actors`.

    Two unrelated mods may both append to a list; appending to a list another unrelated mod replaced
    whole, or removing an item it changed, is an error naming both."""
    for field, items in (patch.get("append") or {}).items():
        holder, key = _parent(civ, field)
        held = holder.get(key)
        if not isinstance(held, list) or not isinstance(items, list):
            raise ModError("mod %s: %s appends to %r which is not a list on civilisation %s" %
                           (manifest.id, path, field, civ.get("id")))
        earlier = claims.get((CIVILIZATION, civ.get("id"), field))
        if _unrelated_claim(earlier, manifest, by_id):
            raise ModError("mods %s and %s both change list %r of civilisation %s; make one depend on "
                           "the other to choose a winner" % (earlier, manifest.id, field, civ.get("id")))
        holder[key] = held + copy.deepcopy(items)
    for field, keys in (patch.get("remove_items") or {}).items():
        holder, key = _parent(civ, field)
        held = holder.get(key)
        if not isinstance(held, list):
            raise ModError("mod %s: %s removes from %r which is not a list on civilisation %s" %
                           (manifest.id, path, field, civ.get("id")))
        missing = [wanted for wanted in keys if wanted not in {_item_key(item) for item in held}]
        if missing:
            raise ModError("mod %s: %s removes missing %s item(s) %s of civilisation %s" %
                           (manifest.id, path, field, ", ".join(map(str, missing)), civ.get("id")))
        holder[key] = [item for item in held if _item_key(item) not in keys]
    return civ


def civ_file_stem(civ_id: str) -> str:
    """File name stem for a civ id; `:` is not portable in file names, `+` stands in."""
    return civ_id.replace(SEPARATOR, "+")


def civ_id_from_stem(stem: str) -> str:
    return stem.replace("+", SEPARATOR)


def mod_civ_ids(manifest: ModManifest) -> List[str]:
    """Civ ids one mod ships or patches, from its file names."""
    directory = os.path.join(manifest.directory, "data", "civilizations")
    if not os.path.isdir(directory):
        return []
    return [civ_id_from_stem(filename[:-5]) for filename in sorted(os.listdir(directory))
            if filename.endswith(".json") and not filename.startswith("_")]


def _mod_files(name: str, manifests: List[ModManifest]) -> Iterable[tuple]:
    for manifest in manifests:
        path = os.path.join(manifest.directory, "data", "civilizations",
                            civ_file_stem(name) + ".json")
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as source:
                yield manifest, path, json.load(source)


def apply_mod_civilization(name: str, base: Optional[Dict[str, Any]],
                           manifests: Iterable[ModManifest]) -> Optional[Dict[str, Any]]:
    """Base civ (or None) with mod files applied in dependency order.

    A file with `"override": true` patches the civ by deep merge, changing only
    the fields it names; any other file defines a new civ and must not collide.
    """
    manifests = list(manifests)
    by_id = {manifest.id: manifest for manifest in manifests}
    claims: Dict[Any, str] = {}
    civ = base
    defined_by = "the base data" if base is not None else ""
    for manifest, path, patch in _mod_files(name, manifests):
        if patch.get("override") is True:
            if civ is None:
                raise ModError("%s overrides missing civilization %r" % (path, name))
            fields = {key: value for key, value in patch.items() if key not in LIST_OPERATORS}
            claim_fields(claims, CIVILIZATION, name, fields, manifest, by_id)
            civ = deep_merge(civ, dict(fields, id=name))
            civ = apply_list_operators(civ, patch, manifest, by_id, claims, path)
            continue
        check_new_id(manifest, name, False, path)
        if civ is not None:
            raise ModError("civilization %s is defined in both %s and %s" %
                           (name, defined_by, path))
        civ, defined_by = patch, path
    return civ


def check_starting_techs(civ: Dict[str, Any], manifests: Iterable[ModManifest],
                         removed: Optional[Dict[str, str]] = None) -> None:
    """A civ may not start with a technology a mod removed."""
    if removed is None:
        removed = scan_removed(manifests, TECH)
    for tech_id in civ.get("starting_techs") or ():
        if tech_id in removed:
            raise ModError("civilization %s starts with tech node %s; mod %s removed it" %
                           (civ.get("id"), tech_id, removed[tech_id]))


def civilization_names(base_dir: str, manifests: Iterable[ModManifest]) -> List[str]:
    """Every base and mod civilisation file name, hidden ones included."""
    names = {filename[:-5] for filename in os.listdir(base_dir)
             if filename.endswith(".json") and not filename.startswith("_")} \
        if os.path.isdir(base_dir) else set()
    for manifest in manifests:
        names.update(mod_civ_ids(manifest))
    return sorted(names)


def check_all_civilizations(base_dir: str, manifests: Iterable[ModManifest]) -> None:
    """Apply mods to every civ and check its starting techs, whether or not anyone picks it."""
    manifests = list(manifests)
    removed = scan_removed(manifests, TECH)
    for name in civilization_names(base_dir, manifests):
        path = os.path.join(base_dir, name + ".json")
        base = None
        if os.path.exists(path):
            with open(path, encoding="utf-8") as source:
                base = json.load(source)
        civ = apply_mod_civilization(name, base, manifests)
        check_starting_techs(civ, manifests, removed)


def is_hidden(civ: Dict[str, Any]) -> bool:
    return civ.get("hidden") is True
