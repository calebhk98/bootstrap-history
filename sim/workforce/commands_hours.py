"""Commands that change the acting seat's hours and the people on its books, sent by the screens, the project steps and the money phase."""
from dataclasses import dataclass
from typing import Optional, Tuple

from sim.assembly.api import Command


@dataclass(frozen=True)
class AllocateHours(Command):
    """The acting seat promises `hours` a year of its own to the active work `target`, replacing any earlier order."""
    target: str
    hours: float


@dataclass(frozen=True)
class ReleaseHours(Command):
    """The acting seat's standing order of hours to `target` is cleared. Answers the hours a year it was, or None."""
    target: str


@dataclass(frozen=True)
class OrderWork(Command):
    """The acting seat sells `hours` a year of its own as `trade` for wages every year, replacing any earlier order."""
    trade: str
    hours: float


@dataclass(frozen=True)
class CancelWork(Command):
    """The acting seat's standing order to sell hours for wages is cleared. Answers the hours a year it was, or None."""


@dataclass(frozen=True)
class DrawTradeHours(Command):
    """The acting seat's projects have drawn `hours` of `trade` this year."""
    trade: str
    hours: float


@dataclass(frozen=True)
class ResetTradeHours(Command):
    """The year's draws on the trades start again from nothing."""


@dataclass(frozen=True)
class SpendDirectorHours(Command):
    """The acting seat's founder has directed work for `hours` more this year."""
    hours: float


@dataclass(frozen=True)
class SettleLivingCost(Command):
    """The year's living cost, `amount` of it, was billed: the wages paid in advance are used up and the bill is added to what the
    seat has paid for living."""
    amount: float


@dataclass(frozen=True)
class SetWageHoursSold(Command):
    """The hours the acting seat has sold for wages this year are `hours` (a figure being tried, then put back)."""
    hours: float


@dataclass(frozen=True)
class BleedStaff(Command):
    """People the acting seat cannot pay leave: artisans fall by the share `bleed` (not below `artisan_floor`), scholars by
    `bleed` times `scholar_discount` (not below `scholar_floor`)."""
    bleed: float
    artisan_floor: float
    scholar_floor: float
    scholar_discount: float


@dataclass(frozen=True)
class DisperseDependants(Command):
    """The acting seat's freedmen leave and its artisans fall to `artisan_retention` of what they were (not below `artisan_floor`)."""
    artisan_floor: float
    artisan_retention: float


@dataclass(frozen=True)
class LoseCrew(Command):
    """A failed venture costs the acting seat its crew: each person of the trades in `crew` ((trade, share lost), in the order
    to roll) is rolled against the game's dice. Answers ((trade, people before, people left), ...)."""
    crew: Tuple[Tuple[str, float], ...]


@dataclass(frozen=True)
class WatchStaff(Command):
    """The payroll of the seat `seat_id` reports each change from now on (a loaded game or a seat switch needs it again), and says
    it changed."""
    seat_id: str


@dataclass(frozen=True)
class SetReserve(Command):
    """The acting seat keeps `craftsmen` and `scholars` spare hands in reserve (None leaves a figure as it is)."""
    craftsmen: Optional[int] = None
    scholars: Optional[int] = None
