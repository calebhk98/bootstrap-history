"""The state the knowledge module owns."""
from dataclasses import dataclass, field
from typing import Dict, Optional, Set


@dataclass
class KnowledgeSeat:
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
