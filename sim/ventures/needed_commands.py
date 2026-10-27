"""Commands the ventures module sends to owners that have not moved into modules yet.

Each is applied by the engine bridge (sim/engine/bridge_ventures.py) exactly as the old code did. When the owner moves it
takes the class into its own package and applies it; this file loses the entry and the importers follow."""
from dataclasses import dataclass

from sim.assembly.api import Command


@dataclass(frozen=True)
class BumpInstitutionUnitsVersion(Command):
	"""Production: the sizes of the scalable institutions changed, so the figures derived from them are stale."""
