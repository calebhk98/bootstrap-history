"""Mod civilisations: new files, override patches of any civ, and starting-tech checks."""
import json
import os
from typing import Any, Dict, Iterable, List, Optional

from .mods import _check_new_id, _deep_merge
from .mods_base import ModError, ModManifest, claim_fields
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
            civ = _deep_merge(civ, dict(patch, id=name))
            continue
        _check_new_id(manifest, name, False, path)
        if civ is not None:
            raise ModError("civilization %s is defined in both %s and %s" %
                           (name, defined_by, path))
        civ, defined_by = patch, path
    return civ


def check_starting_techs(civ: Dict[str, Any], manifests: Iterable[ModManifest]) -> None:
    """A civ may not start with a technology a mod removed."""
    removed = scan_removed(manifests, TECH)
    for tech_id in civ.get("starting_techs") or ():
        if tech_id in removed:
            raise ModError("civilization %s starts with tech node %s; mod %s removed it" %
                           (civ.get("id"), tech_id, removed[tech_id]))


def is_hidden(civ: Dict[str, Any]) -> bool:
    return civ.get("hidden") is True
