"""How much of a technique an onlooker can recover, for every node that does not declare it itself.

A node's own `copy_visibility` (with its `copy_visibility_reason`) in `data/branches` stands. A node that declares
none takes its category's entry from `data/world/copy_visibility.json`, which states what shows and what does not
of the things the category holds; a mod adds or overrides categories in its own `data/copy_visibility.json`. A node
whose category has no entry keeps the count of trades and materials (TRANSITIONAL, CLAUDE.md 4.4), which
`simulator.py validate` counts."""
import json
import os
from typing import Any, Dict, Iterable, List, Mapping

from .mods import get_ordered_mods
from .mods_base import deep_merge

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_FILE = os.path.join(ROOT, "data", "world", "copy_visibility.json")
MODS_DIRECTORY = os.path.join(ROOT, "mods")
BASIS_KEY = "copy_visibility_basis"

_cache: Dict[str, Dict[str, Any]] = {}


def _read(path: str) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as source:
        return json.load(source)  # type: ignore[no-any-return]


def load(mods_directory: str) -> Dict[str, Any]:
    """The base table with every installed mod's overlay applied: {category: {copy_visibility, reason}}."""
    categories = dict(_read(BASE_FILE).get("categories") or {})
    for manifest in get_ordered_mods(mods_directory):
        path = os.path.join(manifest.directory, "data", "copy_visibility.json")
        if os.path.isfile(path):
            categories = deep_merge(categories, _read(path).get("categories") or {})
    return categories


def table() -> Dict[str, Any]:
    """The merged table for the current mods directory, built once."""
    if MODS_DIRECTORY not in _cache:
        _cache.clear()
        _cache[MODS_DIRECTORY] = load(MODS_DIRECTORY)
    return _cache[MODS_DIRECTORY]


def apply_defaults(nodes: Iterable[Dict[str, Any]], categories: Mapping[str, Any]) -> int:
    """Give each node that declares no `copy_visibility` its category's share and reason, marked as taken from
    the category; returns how many were filled."""
    filled = 0
    for node in nodes:
        entry = categories.get(node.get("cat"))
        if "copy_visibility" in node or entry is None:
            continue
        node["copy_visibility"] = entry["copy_visibility"]
        node["copy_visibility_reason"] = entry["reason"]
        node[BASIS_KEY] = "category"
        filled += 1
    return filled


def undeclared(nodes: Mapping[str, Mapping[str, Any]]) -> List[str]:
    """Ids of nodes that still declare no visibility, after the category defaults are applied."""
    return sorted(node_id for node_id, node in nodes.items() if "copy_visibility" not in node)
