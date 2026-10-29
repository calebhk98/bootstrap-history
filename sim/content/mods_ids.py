"""Mod id format, content namespaces, and the declared-dependency check."""
import json
import os
import re
from typing import Any, Dict, Iterable, Iterator, Optional

from .mods_base import ModError, ModManifest, ancestors

# A mod id can never contain the separator, so `<mod_id>:<name>` is owned by exactly one mod.
SEPARATOR = ":"
MOD_ID_PATTERN = r"[a-z][a-z0-9]*(?:_[a-z0-9]+)+_[a-z0-9]{4,}"
LOCAL_NAME_PATTERN = r"[a-z][a-z0-9_]*"
_QUALIFIED = re.compile(r"(%s)%s(%s)" % (MOD_ID_PATTERN, SEPARATOR, LOCAL_NAME_PATTERN))


def check_mod_id(mod_id: Any, path: str) -> None:
    """A mod id is `<author>_<name>_<suffix>` with a random suffix of 4+ characters."""
    if not isinstance(mod_id, str) or not re.fullmatch(MOD_ID_PATTERN, mod_id):
        raise ModError(
            "%s has invalid mod id %r. Use <author>_<name>_<suffix>: lowercase letters, digits "
            "and underscores, starting with a letter, ending in a random suffix of 4 or more "
            "lowercase letters or digits (for example ana_steamage_k3f9), so no two authors "
            "pick the same id. Ids never contain %r; that is the namespace separator."
            % (path, mod_id, SEPARATOR))


def namespaced(mod_id: str, name: str) -> str:
    return mod_id + SEPARATOR + name


def owner_of(item_id: str) -> Optional[str]:
    """The mod id a namespaced content id belongs to, or None for a base id."""
    owner, separator, _name = str(item_id).partition(SEPARATOR)
    return owner if separator else None


def is_mod_content(item_id: str, manifests: Iterable[ModManifest]) -> bool:
    return owner_of(item_id) in {manifest.id for manifest in manifests}


def check_new_id(manifest: ModManifest, item_id: str, override: bool, path: str) -> None:
    """A new content id lives in its own mod's namespace: `<mod_id>:<name>`."""
    if override:
        return
    match = _QUALIFIED.fullmatch(str(item_id))
    if not match or match.group(1) != manifest.id:
        raise ModError("%s introduces id %r outside the namespace of mod %s; new ids must be "
                       "%s%s<name>, or set override=true to patch an existing id" %
                       (path, item_id, manifest.id, manifest.id, SEPARATOR))


def _strings(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, inner in value.items():
            yield str(key)
            yield from _strings(inner)
    elif isinstance(value, list):
        for inner in value:
            yield from _strings(inner)


def _mod_strings(manifest: ModManifest) -> Iterator[tuple]:
    """Every (file, string) in a mod's data files, keys included."""
    for folder, _dirs, files in os.walk(os.path.join(manifest.directory, "data")):
        for filename in sorted(files):
            if not filename.endswith(".json"):
                continue
            path = os.path.join(folder, filename)
            with open(path, encoding="utf-8") as source:
                for text in _strings(json.load(source)):
                    yield path, text


def check_declared_dependencies(manifests: Iterable[ModManifest]) -> None:
    """A mod naming another mod's ids must depend on it, directly or transitively."""
    manifests = list(manifests)
    by_id: Dict[str, ModManifest] = {manifest.id: manifest for manifest in manifests}
    for manifest in manifests:
        allowed = ancestors(manifest, by_id) | {manifest.id}
        for path, text in _mod_strings(manifest):
            match = _QUALIFIED.fullmatch(text)
            if match and match.group(1) in by_id and match.group(1) not in allowed:
                raise ModError("mod %s uses id %s from mod %s (%s) but does not declare it in "
                               "dependencies" % (manifest.id, text, match.group(1), path))
