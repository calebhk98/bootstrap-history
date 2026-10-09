"""Starting kits and win-condition sentences: base data files with installed mods applied."""
import json
import os
from typing import Any, Dict

from .mods import get_ordered_mods
from .mods_world import merge_mod_map

KITS_PATH = "world/starting_kits.json"
LABELS_PATH = "ui/win_condition_labels.json"


def _base(root: str, relative: str, key: str) -> Dict[str, Any]:
    with open(os.path.join(root, "data", *relative.split("/")), encoding="utf-8") as handle:
        return json.load(handle)[key]


def load_starting_kits(root: str, mods_dir: str) -> Dict[str, Dict[str, Any]]:
    return merge_mod_map(_base(root, KITS_PATH, "kits"), get_ordered_mods(mods_dir), KITS_PATH, "kits",
                         "starting kit")


def load_win_condition_labels(root: str, mods_dir: str) -> Dict[str, str]:
    """Metric to sentence template. A metric name belongs to the engine, so a new label is not namespaced."""
    entries = merge_mod_map(_base(root, LABELS_PATH, "labels"), get_ordered_mods(mods_dir), LABELS_PATH,
                            "labels", "win condition label", namespaced=False)
    return {key: entry["text"] for key, entry in entries.items()}
