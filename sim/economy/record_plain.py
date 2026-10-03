"""Dataclasses to plain JSON-ready structures, a copy that shares nothing with the live objects.

Faster than `dataclasses.asdict`, which deep-copies every leaf through generic type checks.
"""
import copy
import dataclasses
from typing import Any, Dict, Tuple

LEAVES = (str, int, float, bool, type(None))
_FIELD_NAMES: Dict[type, Tuple[str, ...]] = {}


def plain(value: Any) -> Any:
    kind = type(value)
    if kind in LEAVES:
        return value
    if kind is dict:
        return {key: (item if type(item) in LEAVES else plain(item)) for key, item in value.items()}
    if kind is list:
        return [plain(item) for item in value]
    if kind is tuple:
        return tuple(plain(item) for item in value)
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        names = _FIELD_NAMES.get(kind)
        if names is None:
            names = _FIELD_NAMES[kind] = tuple(field.name for field in dataclasses.fields(value))
        return {name: plain(getattr(value, name)) for name in names}
    return copy.deepcopy(value)
