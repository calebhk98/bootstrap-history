"""Commands to the owner of the goods market and the agent economy's orders (the markets module)."""
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


@dataclass(frozen=True)
class OpenMarketBook(Command):
	"""Every commodity the price table names gets its book entry, at the society's present output."""


@dataclass(frozen=True)
class RenameMarketSeat(Command):
	"""A seat moved to another id: its place in the year's flows, the agent economy's books and the goods market's seat
	parties follows."""
	from_id: str
	to_id: str


@dataclass(frozen=True)
class MarkMoneyPricedAtEconomy(Command):
	"""The game's money is now counted at the agent economy's unskilled wage."""


@dataclass(frozen=True)
class BuyMaterial(Command):
	"""The acting seat buys `tonnes` of a material at the market (cut to what is offered and affordable); answers the tonnes
	bought."""
	material: str
	tonnes: float


@dataclass(frozen=True)
class SellMaterial(Command):
	"""The acting seat sells `tonnes` of its stock of a material at the market (cut to what is held and absorbed); answers
	the tonnes sold."""
	material: str
	tonnes: float


@dataclass(frozen=True)
class RepriceOpeningMoney(Command):
	"""The agent economy opened and settled its own wage: the game's money, counted until now at the figure `before` (money
	per labour hour), becomes the economy's. Every seat's purse and the tree's money fields move by the ratio of the two,
	and the money is marked as counted at the economy. Applied by the markets module, which asks the ledger to rescale each seat's money and the root to count the tree afresh."""
	before: float


@dataclass(frozen=True)
class FoundBankFromOutside(Command):
	"""The acting seat founds a bank in the agent economy with `capital` in coin, brought in from outside the economy's book.
	Answers the new bank's agent id, or None when the capital buys no units or the economy has not opened."""
	capital: float
