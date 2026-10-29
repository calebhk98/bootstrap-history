"""The foreign-economies file with the economies and untradable materials of every installed mod applied."""
import functools
import json
import os
from typing import Any, Dict, FrozenSet, Tuple

from sim.default_civilisation import REPOSITORY_ROOT

from .mods import get_ordered_mods
from .mods_world import merge_mod_list

FOREIGN_ECONOMIES_PATH = os.path.join(REPOSITORY_ROOT, "data", "world", "foreign_economies.json")
_RELATIVE = "world/foreign_economies.json"


@functools.lru_cache(maxsize=None)
def foreign_economy_document(directory: str, path: str = FOREIGN_ECONOMIES_PATH) -> Dict[str, Any]:
    """{"economies": [...], "not_traded_materials": [...]} after the mods of `directory`; other base keys are kept."""
    with open(path, encoding="utf-8") as handle:
        document = json.load(handle)
    manifests = get_ordered_mods(directory)
    document["economies"] = merge_mod_list(document["economies"], manifests, _RELATIVE,
                                           "economies", "civilization", "foreign economy")
    untraded = list(document.get("not_traded_materials") or ())
    for manifest in manifests:
        mod_path = os.path.join(manifest.directory, "data", "world", "foreign_economies.json")
        if os.path.isfile(mod_path):
            with open(mod_path, encoding="utf-8") as handle:
                untraded.extend(json.load(handle).get("not_traded_materials") or ())
    document["not_traded_materials"] = sorted(set(untraded))
    return document


def foreign_economy_records(directory: str) -> Tuple[Dict[str, Any], ...]:
    """The economies the data file names, with the mods of `directory` applied."""
    return tuple(foreign_economy_document(directory)["economies"])


def not_traded_materials(directory: str) -> FrozenSet[str]:
    """Materials that cannot cross a border, from the data file and the mods of `directory`."""
    return frozenset(foreign_economy_document(directory)["not_traded_materials"])
