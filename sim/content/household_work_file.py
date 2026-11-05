"""Household work data (data/world/household_work.json) with the installed mods applied."""
import os
from typing import Any, Dict

from sim.json_files import read_json

from .mods import get_ordered_mods
from .mods_base import deep_merge


def load_household_work(root: str, mods_dir: str) -> Dict[str, Any]:
    """The base file's tasks and figures, then each mod's file of the same name merged over them in load order."""
    relative = os.path.join("data", "world", "household_work.json")
    merged: Dict[str, Any] = read_json(os.path.join(root, relative))
    for manifest in get_ordered_mods(mods_dir):
        path = os.path.join(manifest.directory, relative)
        if os.path.isfile(path):
            merged = deep_merge(merged, read_json(path))
    return merged
