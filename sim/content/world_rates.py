"""The goods' spoilage rates and service lives with the entries of every installed mod applied: the one loader both are read through."""
import functools
import json
import os
from typing import Any, Dict

from sim.default_civilisation import REPOSITORY_ROOT

from .mods import get_ordered_mods
from .mods_world import merge_mod_map

SPOILAGE_PATH = os.path.join(REPOSITORY_ROOT, "data", "world", "spoilage.json")
SERVICE_LIVES_PATH = os.path.join(REPOSITORY_ROOT, "data", "world", "service_lives.json")


def _entries(directory: str, path: str, collection_key: str, kind: str) -> Dict[str, Any]:
    """The `collection_key` entries of a base file by good id, then each mod's file of the same name: a mod adds a good of
    its own (`<mod id>:<name>`), overrides one (`"override": true`) or removes one (`"remove": true`)."""
    with open(path, encoding="utf-8") as handle:
        base = json.load(handle).get(collection_key) or {}
    return merge_mod_map(base, get_ordered_mods(directory), "world/" + os.path.basename(path), collection_key, kind)


@functools.lru_cache(maxsize=None)
def spoilage_rates(directory: str, path: str = SPOILAGE_PATH) -> Dict[str, float]:
    """{good: continuous decay rate a year} of the goods that spoil, after the mods of `directory`; a good not listed keeps."""
    return {good: float(entry["rate"]) for good, entry in _entries(directory, path, "rates_per_year", "spoilage rate").items()}


@functools.lru_cache(maxsize=None)
def service_life_years(directory: str, path: str = SERVICE_LIVES_PATH) -> Dict[str, float]:
    """{good: years a stock of it serves before it is worn out} after the mods of `directory`; a good not listed is used up
    within the year."""
    return {good: float(entry["years"]) for good, entry in _entries(directory, path, "years", "service life").items()}

