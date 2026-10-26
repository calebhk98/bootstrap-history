"""Renaming an id wherever a store keeps it: as a key, as a value, or as a piece of a composite id.

A seat that leaves a game under another's name (sim/engine/seat_move.py) must leave nothing behind that is
keyed by its id. `rekey` rewrites a container in place and returns it; two keys that become one are merged (numbers
add, mappings and lists join, anything else keeps the newer name's value).
"""
import dataclasses
import re
from typing import Any, Optional, Set

JOINERS = ":#"   # a composite id joins its parts with these: "offer#3" is `<giver id>#<serial>`


def _pattern(old: str):
    return re.compile(r"(^|[%s])%s($|[%s])" % (JOINERS, re.escape(old), JOINERS))


def rename_text(text: str, old: str, new: str) -> str:
    """`text` with `old` replaced where it is the whole text or a whole part of a composite id."""
    if old not in text:
        return text
    pattern = _pattern(old)
    while True:   # a second pass catches parts that shared a joiner with the one just replaced
        renamed = pattern.sub(lambda found: found.group(1) + new + found.group(2), text)
        if renamed == text:
            return text
        text = renamed


def merge_values(kept: Any, other: Any) -> Any:
    """What two values under one key become: sums, joined mappings, joined lists; otherwise `kept`."""
    if isinstance(kept, bool) or isinstance(other, bool):
        return kept
    if isinstance(kept, (int, float)) and isinstance(other, (int, float)):
        return kept + other
    if isinstance(kept, dict) and isinstance(other, dict):
        for key, value in other.items():
            kept[key] = merge_values(kept[key], value) if key in kept else value
        return kept
    if isinstance(kept, list) and isinstance(other, list):
        kept.extend(item for item in other if not isinstance(item, str) or item not in kept)
        return kept
    if isinstance(kept, set) and isinstance(other, set):
        kept |= other
        return kept
    return kept


def rekey(value: Any, old: str, new: str, _seen: Optional[Set[int]] = None) -> Any:
    """`value` with the id `old` renamed to `new` throughout; containers and dataclasses change in place (a frozen
    dataclass is rebuilt), so use the returned value."""
    if isinstance(value, str):
        return rename_text(value, old, new)
    seen = set() if _seen is None else _seen
    if isinstance(value, (dict, list, set, tuple)) or (dataclasses.is_dataclass(value) and not isinstance(value, type)):
        if id(value) in seen:
            return value
        seen.add(id(value))
    if isinstance(value, dict):
        renamed = {}
        for key, item in list(value.items()):
            key = rename_text(key, old, new) if isinstance(key, str) else key
            item = rekey(item, old, new, seen)
            renamed[key] = merge_values(renamed[key], item) if key in renamed else item
        value.clear()
        value.update(renamed)
        return value
    if isinstance(value, list):
        renamed_items = [rekey(item, old, new, seen) for item in value]
        value[:] = [item for position, item in enumerate(renamed_items) if item != new or item not in renamed_items[:position]]
        return value
    if isinstance(value, set):
        renamed_items = {rekey(item, old, new, seen) for item in value}
        value.clear()
        value.update(renamed_items)
        return value
    if isinstance(value, tuple):
        return tuple(rekey(item, old, new, seen) for item in value)
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        changes = {}
        for field in dataclasses.fields(value):
            current = getattr(value, field.name)
            renamed = rekey(current, old, new, seen)
            if renamed is not current:
                changes[field.name] = renamed
        if changes:
            if getattr(type(value), "__dataclass_params__").frozen:
                return dataclasses.replace(value, **changes)
            for name, renamed in changes.items():
                setattr(value, name, renamed)
        return value
    return value
