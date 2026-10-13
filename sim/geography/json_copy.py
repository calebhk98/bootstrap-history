"""A deep copy of JSON-shaped data without `copy.deepcopy`'s memo bookkeeping, for the map's records."""
import copy
from typing import Any


def copied(value: Any) -> Any:
    """`value` with every dict and list rebuilt (no shared or cyclic structure in map data)."""
    if isinstance(value, dict):
        return {key: copied(item) for key, item in value.items()}
    if isinstance(value, list):
        return [copied(item) for item in value]
    return copy.deepcopy(value) if isinstance(value, (set, tuple)) else value
