"""Commands the knowledge module sends to owners that have not moved into modules yet.

Each is applied by the engine bridge (sim/engine/bridge_knowledge.py) exactly as the old code did. When the owner moves
it takes the class into its own package and applies it; this file loses the entry and the importers follow."""
from dataclasses import dataclass

from sim.assembly.api import Command


@dataclass(frozen=True)
class RefreshDoneCaches(Command):
    """Production and the engine's caches: what the acting seat holds has changed, so every figure derived from it
    (revenue, upkeep, capability, material demand) is stale."""
