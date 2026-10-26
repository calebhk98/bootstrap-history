"""Commands to knowledge, the owner of what a seat has learned, lost and heard of."""
from dataclasses import dataclass
from typing import Optional, Tuple

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
class RevealFrom(Command):
    """Finishing `node_id` teaches the acting seat what it leads towards, vaguely. Only under fog."""
    node_id: str


@dataclass(frozen=True)
class RevealNodes(Command):
    """The acting seat has heard of `node_ids`. Answers nothing; hearing never shrinks."""
    node_ids: Tuple[str, ...]
