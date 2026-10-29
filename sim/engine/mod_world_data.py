"""Starting kits: base data files with installed mods applied."""
import json
import os
from typing import Any, Dict

from sim.content.api import get_ordered_mods
from sim.content.api import merge_mod_map

KITS_PATH = "world/starting_kits.json"


def _base(root: str, relative: str, key: str) -> Dict[str, Any]:
    with open(os.path.join(root, "data", *relative.split("/")), encoding="utf-8") as handle:
        return json.load(handle)[key]


def load_starting_kits(root: str, mods_dir: str) -> Dict[str, Dict[str, Any]]:
    return merge_mod_map(_base(root, KITS_PATH, "kits"), get_ordered_mods(mods_dir), KITS_PATH, "kits",
                         "starting kit")
