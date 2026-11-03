"""Commands to the owner of the goods market and the agent economy's orders (the markets module)."""
from dataclasses import dataclass
from typing import Any, Optional

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
class MoveGoods(Command):
	"""`quantity` of `good` at `tile` moves in the economy's book from the account or edge `giver` to `receiver`, for `purpose`.
	A giver that holds less is refused by the book."""
	giver: str
	receiver: str
	good: str
	tile: str
	quantity: float
	purpose: str


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
	"""The acting seat orders `tonnes` of a material at the year's clearing, paying the market no more than `limit_per_tonne` (the
	quote's price when None); carriage to the seat is charged on top when the goods arrive, unless `limit_includes_carriage` says
	the limit already counts it. `project` tags an order a project waits for; `cost_factor` is the project's opposition and
	geography factor on the money. Answers the posted order, or a refusal; the goods arrive when the year clears."""
	material: str
	tonnes: float
	limit_per_tonne: Optional[float] = None
	project: Optional[str] = None
	cost_factor: float = 1.0
	limit_includes_carriage: bool = False


@dataclass(frozen=True)
class SellMaterial(Command):
	"""The acting seat offers `tonnes` of its stock of a material at the year's clearing, taking no less than `limit_per_tonne`
	(the quote when None). Answers the posted order, or a refusal; the proceeds arrive when the year clears."""
	material: str
	tonnes: float
	limit_per_tonne: Optional[float] = None


@dataclass(frozen=True)
class CancelMaterialOrders(Command):
	"""The acting seat withdraws its posted orders to `side` ("buy" or "sell") a material before the year clears. Nothing was
	paid or moved yet. Answers {"cancelled": count, "tonnes": total}, or a refusal when the seat has no such order."""
	side: str
	material: str


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
