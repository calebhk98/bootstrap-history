"""The state the knowledge module owns."""
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class KnowledgeSeat:
    # node id -> the year the seat lost it (a sacking took it); a node absent from `done` and present here is being rebuilt
    forgotten: Dict[str, int] = field(default_factory=dict)
