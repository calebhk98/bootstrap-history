"""Commands the projects module sends to owners that have not moved into modules yet.

Each is applied by the engine bridge (sim/engine/bridge_projects.py) exactly as the old code did. When the owner moves
it takes the class into its own package and applies it; this file loses the entry and the importers follow."""
from dataclasses import dataclass

from sim.assembly.api import Command


@dataclass(frozen=True)
class ClearMothball(Command):
    """Ventures: forget a stale mothball entry for a work that is being built again."""
    node_id: str


@dataclass(frozen=True)
class CompleteProject(Command):
    """Projects' own completion (not moved yet): finish the project at once, as an instantaneous capability does."""
    node_id: str
