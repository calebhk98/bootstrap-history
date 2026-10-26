"""Commands to the owner of who holds each tile."""
from dataclasses import dataclass
from typing import Optional

from sim.assembly.api import Command


@dataclass(frozen=True)
class TransferTile(Command):
	"""Give a tile to a country or seat (`to_actor` None releases it) at a control level (None keeps the level the
	transfer rule picks). Answers the previous owner; the world event log records it with `cause`."""
	tile: str
	to_actor: Optional[str]
	cause: str
	control: Optional[str] = None
