"""Commands to knowledge, the owner of what a seat has learned, lost and heard of."""
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from sim.assembly.api import Command


@dataclass(frozen=True)
class LearnTechnique(Command):
    """The acting seat now holds `node_id`. `granted` marks it as its country's own (never earned, never lost to a
    sack); `year`, when given, records the year it was finished. Idempotent: learning what is held changes nothing but
    still tells the caches."""
    node_id: str
    year: Optional[int] = None
    granted: bool = False


@dataclass(frozen=True)
class ForgetTechnique(Command):
    """The acting seat no longer holds `node_ids`. `year`, when given, records them as lost in that year (a sacking),
    which is what a rebuild is priced from."""
    node_ids: Tuple[str, ...]
    year: Optional[int] = None


@dataclass(frozen=True)
class NoteTechniquesChanged(Command):
    """The acting seat's held set was changed by code outside this module (a re-derived tree, a seat switch, a load), so the
    `techniques_version` moves and every memo keyed on it is stale."""


@dataclass(frozen=True)
class RevealFrom(Command):
    """Finishing `node_id` teaches the acting seat what it leads towards, vaguely. Only under fog."""
    node_id: str


@dataclass(frozen=True)
class RevealNodes(Command):
    """The acting seat has heard of `node_ids`. Answers nothing; hearing never shrinks."""
    node_ids: Tuple[str, ...]


@dataclass(frozen=True)
class ReceiveTechniques(Command):
    """The acting seat is handed `node_ids` complete, by an exchange or a licence (`granted`: held as its society's own). Held
    exactly as `LearnTechnique` holds a node: how a technique was acquired does not change what the seat holds or what is told."""
    node_ids: Tuple[str, ...]
    granted: bool = False
    year: Optional[int] = None       # the year received, kept as each node's finish year unless an earlier one is held


@dataclass(frozen=True)
class StartDoneYearRecord(Command):
    """The acting seat begins recording the year each node is finished, from an empty record."""


@dataclass(frozen=True)
class HandOverTechniques(Command):
    """Seat `to_seat_id` takes over seat `from_seat_id`'s state: what `to_seat_id` held (nodes, granted set, heard-of nodes, finish years; the earlier
    year wins for a node both date) joins what `from_seat_id` holds, since the leaver's knowledge record is the one that moves. Answers how many nodes the leaver then holds."""
    from_seat_id: str
    to_seat_id: str


@dataclass(frozen=True)
class ReplaceTree(Command):
    """The game's tech tree is now `nodes`, node data by id in the tree's own order. Sent when the game is built and each time the
    engine re-derives the nodes' money; the module keeps the object itself, so the views answer with it."""
    nodes: Dict[str, Dict[str, Any]]
