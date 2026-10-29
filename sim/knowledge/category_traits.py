"""Per-category traits, read from data so the engine never names a category.

The base catalogue is `data/world/category_traits.json`; a mod adds or overrides entries in its own
`data/category_traits.json` (same shape): `categories` merges per category and per trait, `diffusion_traits` replaces an entry
with the same `trait` or appends a new one after the base entries. Every function takes the mods directory or the catalogue
it works over; nothing here remembers a directory.
"""
import json
import os
from typing import Any, Dict, Iterable, List, Mapping

from sim.content.api import deep_merge, get_ordered_mods

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_FILE = os.path.join(ROOT, "data", "world", "category_traits.json")


def _read(path: str) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as source:
        return json.load(source)


def _merge_diffusion(entries: List[Dict[str, Any]], patch: Iterable[Dict[str, Any]]) -> None:
    for entry in patch:
        for position, existing in enumerate(entries):
            if existing["trait"] == entry["trait"]:
                entries[position] = deep_merge(existing, entry)
                break
        else:
            entries.append(dict(entry))


def load(mods_directory: str) -> Dict[str, Any]:
    """The base catalogue with every installed mod's overlay applied."""
    base = _read(BASE_FILE)
    merged = {"categories": dict(base["categories"]),
              "diffusion_traits": [dict(entry) for entry in base["diffusion_traits"]]}
    for manifest in get_ordered_mods(mods_directory):
        path = os.path.join(manifest.directory, "data", "category_traits.json")
        if not os.path.isfile(path):
            continue
        overlay = _read(path)
        merged["categories"] = deep_merge(merged["categories"], overlay.get("categories") or {})
        _merge_diffusion(merged["diffusion_traits"], overlay.get("diffusion_traits") or ())
    return merged


def has_trait(catalogue: Mapping[str, Any], category: Any, trait: str) -> bool:
    """Whether the category's entry sets this flag; a category with no entry has none."""
    return bool(catalogue["categories"].get(category, {}).get(trait))


def diffusion_traits(catalogue: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Diffusion trait entries by trait name, in priority order."""
    return {entry["trait"]: entry for entry in catalogue["diffusion_traits"]}


def categories_without_traits(catalogue: Mapping[str, Any], nodes: Iterable[Mapping[str, Any]]) -> List[str]:
    """Categories some node uses that the catalogue has no entry for."""
    known = catalogue["categories"]
    return sorted({node["cat"] for node in nodes if node.get("cat") and node["cat"] not in known})


def check_category_traits(nodes: Iterable[Mapping[str, Any]], mods_directory: str) -> List[str]:
    """Validation errors: a node category with no traits entry, over the catalogue of `mods_directory`."""
    return ["category %r is used by a node but has no entry in data/world/category_traits.json "
            "(a mod adds its own in data/category_traits.json)" % category
            for category in categories_without_traits(load(mods_directory), nodes)]
