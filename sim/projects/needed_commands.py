"""Commands the projects module sends to owners that have not moved into modules yet.

Each is applied by the engine bridge (sim/engine/bridge_projects.py) exactly as the old code did. When the owner moves
it takes the class into its own package and applies it; this file loses the entry and the importers follow."""
from dataclasses import dataclass

from sim.assembly.api import Command


@dataclass(frozen=True)
class NoteConcernChange(Command):
    """The cause book (why a number moved) records that a concern opened or closed: `kind` is "opening" or "closure",
    `cause` the reason, and the row carries what the node earns and costs a year."""
    kind: str
    node_id: str
    cause: str
