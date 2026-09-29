"""Mod civilisations: new files, override patches of any civ, and starting-tech checks."""
import json
import os
from typing import Any, Dict, Iterable, List, Optional

from .mods import _check_new_id
from .mods_base import ModError, ModManifest, claim_fields, deep_merge
from .mods_remove import TECH, scan_removed

CIVILIZATION = "civilization"


def _mod_files(name: str, manifests: List[ModManifest]) -> Iterable[tuple]:
    for manifest in manifests:
        path = os.path.join(manifest.directory, "data", "civilizations", name + ".json")
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
            claim_fields(claims, CIVILIZATION, name, patch, manifest, by_id)
            civ = deep_merge(civ, dict(patch, id=name))
            continue
        _check_new_id(manifest, name, False, path)
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
    names = set()
    directories = [base_dir] + [os.path.join(manifest.directory, "data", "civilizations")
                                for manifest in manifests]
    for directory in directories:
        if os.path.isdir(directory):
            names.update(filename[:-5] for filename in os.listdir(directory)
                         if filename.endswith(".json") and not filename.startswith("_"))
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
