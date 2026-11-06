"""What the economy keeps about people who are not free to move or to keep their wage: bonds for debt, bought bonded
people employers hold, and the people who fled a labour area."""
from dataclasses import dataclass, field
from typing import Any, Dict

from .record_parts import OwnedRecord
from .types import AgentId, TileId, TradeId


@dataclass
class UnfreeRecord(OwnedRecord):
    bondage: Dict[AgentId, Dict[str, Any]] = field(default_factory=dict)   # household cohort -> creditor, debt left, years left (bondage.py)
    bonded_held: Dict[TileId, Dict[TradeId, Dict[AgentId, float]]] = field(default_factory=dict)   # tile -> trade -> employer -> bought bonded people it holds (bondage_hours.py)
    fugitives: Dict[str, Dict[str, Any]] = field(default_factory=dict)   # labour area people fled from -> people still away, arrears owed per head, the area they went to (flight_year.py)

    OWNERS = ("unfree_record", "bondage", "bondage_hours")
    AGENT_KEYED = ("bondage", "bonded_held")
    SAVED_SORTED = ("bondage", "fugitives")
