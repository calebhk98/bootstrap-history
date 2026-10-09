"""The foreign-economies file with every installed mod's economies and untradable materials applied."""
import functools
import json
import os

from .data import MODDIR, ROOT
from .mods import get_ordered_mods
from .mods_world import merge_mod_list

FOREIGN_ECONOMIES_PATH = os.path.join(ROOT, "data", "world", "foreign_economies.json")
_RELATIVE = "world/foreign_economies.json"


@functools.lru_cache(maxsize=None)
def foreign_economy_document():
    """{"economies": [...], "not_traded_materials": [...]} after mods; other base keys are kept."""
    with open(FOREIGN_ECONOMIES_PATH, encoding="utf-8") as handle:
        document = json.load(handle)
    manifests = get_ordered_mods(MODDIR)
    document["economies"] = merge_mod_list(document["economies"], manifests, _RELATIVE,
                                           "economies", "civilization", "foreign economy")
    untraded = list(document.get("not_traded_materials") or ())
    for manifest in manifests:
        path = os.path.join(manifest.directory, "data", "world", "foreign_economies.json")
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as handle:
                untraded.extend(json.load(handle).get("not_traded_materials") or ())
    document["not_traded_materials"] = sorted(set(untraded))
    return document
