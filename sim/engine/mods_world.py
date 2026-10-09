"""Mod entries for small keyed data files: add, override (deep merge) or remove by id."""
import copy
import json
import os
from typing import Any, Dict, Iterable, List

from .mods_base import (ModError, ModManifest, check_not_removed, claim_fields, claim_removal,
                        deep_merge)
from .mods_ids import check_new_id


def _read_entries(manifest: ModManifest, relative_path: str, collection_key: str):
    path = os.path.join(manifest.directory, "data", *relative_path.split("/"))
    if not os.path.isfile(path):
        return path, None
    with open(path, encoding="utf-8") as source:
        document = json.load(source)
    entries = document.get(collection_key) or {}
    if not isinstance(entries, dict):
        raise ModError("%s: %r must be an object keyed by id" % (path, collection_key))
    return path, entries


def merge_mod_map(base: Dict[str, Any], manifests: Iterable[ModManifest], relative_path: str,
                  collection_key: str, kind: str, namespaced: bool = True) -> Dict[str, Any]:
    """`base` (id to entry) with every mod's file applied in dependency order.

    An entry with `"remove": true` deletes an existing id; `"override": true` deep-merges over an
    existing id; any other entry is new. A new id must be `<mod_id>:<name>` when `namespaced`."""
    merged = copy.deepcopy(base)
    manifests = list(manifests)
    by_id = {manifest.id: manifest for manifest in manifests}
    claims: Dict[Any, str] = {}
    for manifest in manifests:
        path, entries = _read_entries(manifest, relative_path, collection_key)
        for entry_id, entry in (entries or {}).items():
            if entry.get("remove") is True:
                if entry_id not in merged:
                    raise ModError("mod %s: %s removes missing %s %r" % (manifest.id, path, kind, entry_id))
                claim_removal(claims, kind, entry_id, manifest, by_id)
                del merged[entry_id]
            elif entry.get("override") is True:
                check_not_removed(claims, kind, entry_id, manifest, by_id)
                if entry_id not in merged:
                    raise ModError("mod %s: %s overrides missing %s %r" % (manifest.id, path, kind, entry_id))
                claim_fields(claims, kind, entry_id, entry, manifest, by_id)
                merged[entry_id] = deep_merge(merged[entry_id], entry)
            else:
                if namespaced:
                    check_new_id(manifest, entry_id, False, path)
                if entry_id in merged:
                    raise ModError("%s %s is defined before %s; use override or remove to change it" %
                                   (kind, entry_id, path))
                merged[entry_id] = deep_merge({}, entry)
    return merged


def merge_mod_list(base: List[Dict[str, Any]], manifests: Iterable[ModManifest], relative_path: str,
                   collection_key: str, key_field: str, kind: str) -> List[Dict[str, Any]]:
    """The same rules for a list of records identified by `key_field` (the key is not namespaced)."""
    manifests = list(manifests)
    by_id = {manifest.id: manifest for manifest in manifests}
    claims: Dict[Any, str] = {}
    merged = [copy.deepcopy(record) for record in base]
    for manifest in manifests:
        path = os.path.join(manifest.directory, "data", *relative_path.split("/"))
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as source:
            records = json.load(source).get(collection_key) or []
        for record in records:
            key = record.get(key_field)
            position = next((i for i, held in enumerate(merged) if held.get(key_field) == key), None)
            if record.get("remove") is True:
                if position is None:
                    raise ModError("mod %s: %s removes missing %s %r" % (manifest.id, path, kind, key))
                claim_removal(claims, kind, key, manifest, by_id)
                del merged[position]
            elif record.get("override") is True:
                check_not_removed(claims, kind, key, manifest, by_id)
                if position is None:
                    raise ModError("mod %s: %s overrides missing %s %r" % (manifest.id, path, kind, key))
                claim_fields(claims, kind, key, {name: value for name, value in record.items() if name != key_field},
                             manifest, by_id)
                merged[position] = deep_merge(merged[position], record)
            elif position is not None:
                raise ModError("%s %s is defined before %s; use override or remove to change it" % (kind, key, path))
            else:
                merged.append(deep_merge({}, record))
    return merged
