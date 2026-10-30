"""Mod overrides of declared numbers (`declare` in sim/constants.py): the rules a mod may retune.

A mod's `data/constants.json` is `{"constants": {"NAME": {"value": ..., "why": "..."}}}`. The value replaces the
declared one wherever `declare` is called, whatever its kind; `why` says what the mod's world is doing differently.
Two unrelated mods overriding one name are an error naming both (a mod that depends on the other wins). A name no
module declares is reported by `simulator.py validate`.
"""
import functools
import json
import os
from typing import Any, Dict, NamedTuple, Optional

from .mods import get_ordered_mods
from .mods_base import ModError, claim_fields

REPOSITORY = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONSTANTS_FILE = os.path.join("data", "constants.json")


class ConstantOverride(NamedTuple):
    mod_id: str
    value: Any
    why: str
    path: str


def _same_shape(declared: Any, given: Any) -> bool:
    """A number may replace a number (int and float alike), a bool a bool; anything else must match its type."""
    if isinstance(declared, bool) or isinstance(given, bool):
        return isinstance(declared, bool) and isinstance(given, bool)
    if isinstance(declared, (int, float)):
        return isinstance(given, (int, float))
    return type(declared) is type(given)


@functools.lru_cache(maxsize=None)
def constant_overrides(mods_dir: Optional[str] = None) -> Dict[str, ConstantOverride]:
    """{declared name: override} from every installed mod in load order."""
    mods_dir = mods_dir or os.path.join(REPOSITORY, "mods")
    manifests = get_ordered_mods(mods_dir)
    by_id = {manifest.id: manifest for manifest in manifests}
    claims: Dict[Any, str] = {}
    found: Dict[str, ConstantOverride] = {}
    for manifest in manifests:
        path = os.path.join(manifest.directory, CONSTANTS_FILE)
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as source:
            entries = json.load(source).get("constants") or {}
        for name, entry in entries.items():
            if not isinstance(entry, dict) or "value" not in entry or not str(entry.get("why", "")).strip():
                raise ModError("%s: constant %s needs an object with a 'value' and a 'why'" % (path, name))
            claim_fields(claims, "declared constant", name, {"value": entry["value"]}, manifest, by_id)
            found[name] = ConstantOverride(manifest.id, entry["value"], str(entry["why"]).strip(), path)
    return found


def apply_override(name: str, declared: Any, mods_dir: Optional[str] = None) -> Optional[ConstantOverride]:
    """The mod override of this declared number, checked to have the declared value's shape; None for none."""
    override = constant_overrides(mods_dir).get(name)
    if override is not None and not _same_shape(declared, override.value):
        raise ModError("%s: constant %s is declared as %r; the override %r is not the same kind of value" %
                       (override.path, name, declared, override.value))
    return override
