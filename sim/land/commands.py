"""Commands to the owner of who holds each tile and of the colonies."""
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


@dataclass(frozen=True)
class AdvanceColonies(Command):
	"""One year for every seat's colonies in `year`: the people work the land they can hold and eat what it gives; a colony
	whose people die out is lost."""
	year: int


@dataclass(frozen=True)
class FoundColony(Command):
	"""The acting seat founds a colony on `tile`: the outfit is paid, the settlers leave the country and the tile is held at the
	settlement level. Answers {tile, settlers, cost, text}, or a Refusal whose cause is tile_held, unreachable,
	no_settlement_work, too_few_people or cannot_afford."""
	tile: str


@dataclass(frozen=True)
class FinishWays(Command):
	"""Open the ways whose build time has passed, so routes, reach and the economy's carriage see them (the works register finishes
	on the same beat). Sent at the start of the market phase; answers nothing."""
