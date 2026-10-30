"""Living stock's commands: what any actor sends to change a held herd or to buy one abroad."""
from dataclasses import dataclass

from sim.assembly.api import Command


@dataclass(frozen=True)
class ChangeHeld(Command):
	"""Units of a stock material added to (positive) or taken from (negative) the acting seat's held stock: births, a
	gift, a founding herd, a loss, a draw. The tonnes go through the ledger's `ChangeStock`."""
	material: str
	units: float


@dataclass(frozen=True)
class GrantOpeningStock(Command):
	"""Credit what the civilisation held at its date."""


@dataclass(frozen=True)
class GrantOpeningHerds(Command):
	"""Credit the opening herds the economy's herd producers keep, held to the pasture the held tiles carry, and record
	them as the society's own head."""


@dataclass(frozen=True)
class BuyStock(Command):
	"""Pay a quoted purchase from a partner (`stock_purchase_quote`) and receive the stock. Answers True, or a refusal
	with cause `cannot_afford`."""
	material: str
	partner: str
	tonnes: float
	cost: float


@dataclass(frozen=True)
class SmuggleStock(Command):
	"""Carry stock out of a partner that will not sell it (`stock_smuggle_quote`): pay the carrying, draw for the state's
	catching, then deliver or punish. Answers the outcome (the terms plus `caught`, `delivered_units`, `closed_until`),
	or a refusal with cause `cannot_afford`."""
	material: str
	partner: str
	units: float
	tonnes: float
	cost: float
	arrives_units: float
	chance_caught: float
