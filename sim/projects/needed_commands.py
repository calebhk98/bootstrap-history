"""Commands the projects module sends to owners that have not moved into modules yet.

Each is applied by the engine bridge (sim/engine/bridge_projects.py) exactly as the old code did. When the owner moves
it takes the class into its own package and applies it; this file loses the entry and the importers follow."""
from dataclasses import dataclass
from typing import Optional

from sim.assembly.api import Command


@dataclass(frozen=True)
class ClearMothball(Command):
    """Ventures: forget a stale mothball entry for a work that is being built again."""
    node_id: str


@dataclass(frozen=True)
class NoteConcernChange(Command):
    """The cause book (why a number moved) records that a concern opened or closed: `kind` is "opening" or "closure",
    `cause` the reason, and the row carries what the node earns and costs a year."""
    kind: str
    node_id: str
    cause: str


@dataclass(frozen=True)
class NoteYearSpend(Command):
    """The acting seat's count of what it paid on projects this year (the year's close moves it to last year's), beside
    the payment that moved it; applied by the engine bridge until the cash book moves into the ledger."""
    amount: float


@dataclass(frozen=True)
class OpenVenture(Command):
    """Ventures: open a completed concern's doors (at `units` of an institution's capacity when given), as `open` does.
    Answers (did it open, the reply: a sentence, a Refusal or a LogLine)."""
    node_id: str
    units: Optional[float] = None
