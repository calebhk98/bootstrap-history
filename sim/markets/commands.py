"""Commands to the owner of the goods market's year (markets, not moved yet: the bridge applies them)."""
from dataclasses import dataclass

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
