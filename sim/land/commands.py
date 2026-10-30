"""Commands to the owner of who holds each tile, the ways and works built, and the colonies."""
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


@dataclass(frozen=True)
class BuildWay(Command):
	"""The acting seat's household builds `way` ("road", "rail", "canal", "bridge", "sea_canal", or "port" on one tile, named
	twice) between two bordering tiles its nation holds: the quote is paid, a crew is taken from the labour market and the way
	opens when its build time has passed. Answers (ok, text); a failure's text is a Refusal when it has a cause."""
	tile_a: str
	tile_b: str
	way: str


@dataclass(frozen=True)
class BuildWork(Command):
	"""The acting seat's household builds `capacity` of the known construction `node` on a tile its nation holds. Answers
	(ok, text)."""
	tile: str
	node: str
	capacity: float = 1.0


@dataclass(frozen=True)
class LoseWork(Command):
	"""Take up to `capacity` of a work away from a tile (destroyed, abandoned, sacked). Answers nothing."""
	tile: str
	node: str
	capacity: float
