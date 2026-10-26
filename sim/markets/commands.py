"""Commands to the owner of the goods market's year (markets, not moved yet: the bridge applies them)."""
from dataclasses import dataclass
from typing import Any

from sim.assembly.api import Command


@dataclass(frozen=True)
class ResetDraws(Command):
    """Start a fresh count of what running works draw from the market's standing offer this year."""


@dataclass(frozen=True)
class NoteDraw(Command):
    """Running works used `tonnes` of a commodity the seat neither held nor made; nothing for tonnes that are not positive."""
    commodity: str
    tonnes: float


@dataclass(frozen=True)
class NotePurchase(Command):
    """The acting seat bought `tonnes` of a commodity at the market this year (counted in the book; the money and the
    goods move by the ledger's commands); nothing for tonnes that are not positive."""
    commodity: str
    tonnes: float


@dataclass(frozen=True)
class ForgetActorOrders(Command):
	"""An actor's sales and purchases noted for this year's market end; it deals afresh."""
	actor_id: str


@dataclass(frozen=True)
class NoteActorSale(Command):
	"""An actor offers `tonnes` of a material to the agent economy's market this year; `from_concerns`, [(node id, tonnes)],
	names the concerns that made it (it will not sell below what they cost it to make), or None."""
	seller_id: str
	material: str
	tonnes: float
	from_concerns: Any = None


@dataclass(frozen=True)
class NoteActorPurchase(Command):
	"""An actor bids for `tonnes` of a commodity in the agent economy's market this year, paying up to `budget` in coin."""
	buyer_id: str
	commodity: str
	tonnes: float
	budget: float = 0.0
