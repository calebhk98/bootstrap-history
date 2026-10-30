"""The sentence templates for a win condition's metric: the base file with every installed mod's labels applied."""
import json
import os
from typing import Dict

from sim.default_civilisation import REPOSITORY_ROOT

from .mods import get_ordered_mods
from .mods_world import merge_mod_map

LABELS_PATH = "ui/win_condition_labels.json"


def load_win_condition_labels(root: str, mods_dir: str) -> Dict[str, str]:
    """Metric to sentence template. A metric name belongs to the engine, so a new label is not namespaced."""
    with open(os.path.join(root, "data", *LABELS_PATH.split("/")), encoding="utf-8") as handle:
        base = json.load(handle)["labels"]
    entries = merge_mod_map(base, get_ordered_mods(mods_dir), LABELS_PATH, "labels", "win condition label", namespaced=False)
    return {key: entry["text"] for key, entry in entries.items()}


def win_condition_labels(directory: str) -> Dict[str, str]:
    """The templates of the game over the mods of `directory`."""
    return load_win_condition_labels(REPOSITORY_ROOT, directory)
