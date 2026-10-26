"""Commands to the owner of the world event log (`state.economy.world_events`, shared by every seat)."""
from dataclasses import dataclass, field
from typing import Any, Dict, Tuple

from sim.assembly.api import Command


@dataclass(frozen=True)
class RecordWorldEvent(Command):
	"""A dated record of what changed in the world and why, stamped with the game's year. Answers the record written."""
	kind: str
	actors: Tuple[str, ...] = ()
	tiles: Tuple[str, ...] = ()
	cause: str = ""
	facts: Dict[str, Any] = field(default_factory=dict)
