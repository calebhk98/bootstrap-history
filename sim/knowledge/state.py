"""The state the knowledge module owns."""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set

from .held import check_writing, held_map, held_set

_SETS = ("done", "granted", "revealed")
_MAPS = ("done_year", "forgotten")


@dataclass
class KnowledgeSeat:
    """Every field is changed only by the module's commands: the containers, and the fields themselves once built, refuse any
    other write (`held.py`)."""
    # the nodes the seat holds, finished or granted
    done: Set[str] = field(default_factory=set)
    # the held nodes its country already had: never counted as earned, never lost to a sack
    granted: Set[str] = field(default_factory=set)
    # node id -> the year the seat finished it; None until a run starts recording
    done_year: Optional[Dict[str, int]] = None
    # the nodes the seat has heard of under fog
    revealed: Set[str] = field(default_factory=set)
    # node id -> the year the seat lost it (a sacking took it); a node absent from `done` and present here is being rebuilt
    forgotten: Dict[str, int] = field(default_factory=dict)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in _SETS:
            value = held_set(value)
        elif name in _MAPS:
            value = held_map(value)
        else:
            object.__setattr__(self, name, value)
            return
        if name in self.__dict__:   # the first assignment is the build
            check_writing()
        object.__setattr__(self, name, value)
