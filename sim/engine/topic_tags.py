"""Topic tags: broad groupings of node categories, from data/world/topic_tags.json and mods.

A mod adds a tag (id namespaced as `<mod_id>:<name>`) or extends an existing tag's
categories and words. Merging is additive.
"""

import json
import os
from typing import Dict, Optional

from .mods import ModError, get_ordered_mods
from .mods_ids import check_new_id

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_mods_dir = os.path.join(_ROOT, "mods")
_cache: Optional[Dict[str, Dict[str, tuple]]] = None


def _read(path):
    with open(path, encoding="utf-8") as source:
        return json.load(source).get("tags") or {}


def load_topic_tags(root: str, mods_dir: Optional[str] = None) -> Dict[str, Dict[str, tuple]]:
    """Base tags, then each mod's, in dependency order."""
    mods_dir = mods_dir or os.path.join(root, "mods")
    merged: Dict[str, Dict[str, list]] = {}

    def merge(path, manifest):
        if not os.path.isfile(path):
            return
        for tag, spec in _read(path).items():
            if not isinstance(spec, dict):
                raise ModError("%s: tag %r must be an object with cats and words" % (path, tag))
            if tag not in merged:
                if manifest:
                    check_new_id(manifest, tag, False, path)
                merged[tag] = {"cats": [], "words": []}
            for key in ("cats", "words"):
                for item in spec.get(key) or ():
                    if item not in merged[tag][key]:
                        merged[tag][key].append(item)

    merge(os.path.join(root, "data", "world", "topic_tags.json"), None)
    for manifest in get_ordered_mods(mods_dir):
        merge(os.path.join(manifest.directory, "data", "world", "topic_tags.json"), manifest)
    return {tag: {key: tuple(values) for key, values in spec.items()}
            for tag, spec in merged.items()}


def current() -> Dict[str, Dict[str, tuple]]:
    """The tags for the active mods directory, loaded once."""
    global _cache
    if _cache is None:
        _cache = load_topic_tags(_ROOT, _mods_dir)
    return _cache


def use_mods_dir(mods_dir: Optional[str]) -> None:
    """Point at another mods directory (None for the default) and reload."""
    global _cache, _mods_dir
    _mods_dir = mods_dir or os.path.join(_ROOT, "mods")
    _cache = None
