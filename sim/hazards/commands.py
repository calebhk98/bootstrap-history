"""Commands to hazards: the owner of the world event log and the world's output factor."""
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


@dataclass(frozen=True)
class LoseCapital(Command):
	"""A catastrophe destroys `fraction` of what the acting household holds, never of what it owes. Answers the money
	destroyed."""
	fraction: float
	cause: str = "losses"


@dataclass(frozen=True)
class RecoverOutput(Command):
	"""The year's recovery of the world's output factor toward normal, faster the stronger the state's military."""


@dataclass(frozen=True)
class SayOnce(Command):
	"""The notice named `key` is marked as told. Answers True the first time it is sent and False after, so the sender tells its
	players once."""
	key: str
